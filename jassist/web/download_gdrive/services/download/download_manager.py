"""
Download Manager module.

This module serves as the orchestration layer for the download process.
It coordinates the interactions between the Google Drive client, file filtering,
file downloading, file system operations, and schedule evaluation.
"""
import logging
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
from django.utils import timezone
from django.contrib.auth.models import User

from ...models import UserDriveConfig, DownloadRecord, UserTranscriptionConfig, TranscriptionJob
from .google_drive_client import GoogleDriveClient
from .file_filter import FileFilter
from .file_downloader import FileDownloader
from .file_system_handler import FileSystemHandler
from .schedule_evaluator import ScheduleEvaluator
from ..transcription.transcription_manager import TranscriptionManager

# Create a logger
logger = logging.getLogger(__name__)

class DownloadManager:
    """
    Orchestrates the download process for Google Drive files.
    """
    def __init__(self, user_id: int, dry_run: bool = False, auto_transcribe: bool = True):
        """
        Initialize the download manager for a specific user.
        
        Args:
            user_id (int): User ID
            dry_run (bool): If True, no actual downloads or deletions will occur
            auto_transcribe (bool): If True, will attempt to transcribe audio files after download
        """
        self.user_id = user_id
        self.dry_run = dry_run
        self.auto_transcribe = auto_transcribe
        self.user = User.objects.get(id=user_id)
        self.stats = {
            "folders_processed": 0,
            "files_found": 0,
            "files_downloaded": 0,
            "files_deleted": 0,
            "files_transcribed": 0,
            "errors": 0
        }
        
        # Initialize user configuration
        self._initialize_user_config()
        
        # Initialize components
        self.drive_client = GoogleDriveClient(self.user)
        self.file_filter = FileFilter(self.config)
        self.file_system = FileSystemHandler(self.user_id, self.config)
        self.file_downloader = FileDownloader(self.drive_client, self.file_system, self.dry_run)
        self.schedule_evaluator = ScheduleEvaluator()
    
    def _initialize_user_config(self):
        """Initialize and validate user configuration."""
        try:
            self.user_config = UserDriveConfig.objects.get(user_id=self.user_id)
            
            # Check if user has active configuration
            if not self.user_config.is_active:
                logger.warning(f"Drive downloads disabled for user: {self.user.username}")
                raise ValueError("Drive downloads are disabled for this user")
                
            # Combine global and user settings
            self.config = self.user_config.get_combined_config()
            
        except UserDriveConfig.DoesNotExist:
            logger.error(f"No drive configuration found for user: {self.user_id}")
            raise ValueError(f"No drive configuration found for user: {self.user_id}")
        
        # Check if transcription is available for this user
        self.transcription_available = False
        if self.auto_transcribe:
            try:
                self.transcription_config = UserTranscriptionConfig.objects.get(
                    user_id=self.user_id, 
                    is_active=True
                )
                self.transcription_available = True
                logger.debug(f"Transcription is available for user: {self.user.username}")
            except UserTranscriptionConfig.DoesNotExist:
                logger.debug(f"Transcription not configured for user: {self.user.username}")
    
    def run_downloads(self, force: bool = False) -> Dict[str, Any]:
        """
        Run the download process for the user.
        
        Args:
            force (bool): If True, ignore schedule and run anyway
            
        Returns:
            Dict[str, Any]: Statistics about the download process
        """
        try:
            logger.info(f"Starting Drive download for user: {self.user.username}")
            
            if self.dry_run:
                logger.info("Running in DRY RUN mode - no actual changes will be made")
            
            # Check if we should run now based on schedule (unless forced)
            if not force and not self.schedule_evaluator.should_run_now(
                self.user_config.download_schedule, 
                self.user_config.last_run
            ):
                logger.info(f"Skipping download for user {self.user.username} - not scheduled to run now")
                return {
                    "success": True,
                    "message": "Download skipped - not scheduled to run now",
                    "stats": self.stats
                }
            
            # Process each target folder
            target_folders = self.config['folders']['target_folders']
            if not target_folders:
                logger.warning(f"No target folders specified for user: {self.user.username}")
                return {"error": "No target folders specified", "stats": self.stats}
            
            for folder_name in target_folders:
                try:
                    self._process_folder(folder_name)
                except Exception as e:
                    logger.error(f"Error processing folder {folder_name}: {e}")
                    logger.debug(traceback.format_exc())
                    self.stats["errors"] += 1
            
            # Update last run time
            if not self.dry_run:
                self.user_config.last_run = timezone.now()
                self.user_config.save()
                
            logger.info(f"Completed Drive download for user: {self.user.username}")
            logger.info(f"Stats: {self.stats}")
            
            return {
                "success": self.stats["errors"] == 0,
                "message": "Download completed successfully" if self.stats["errors"] == 0 else "Download completed with errors",
                "stats": self.stats
            }
            
        except Exception as e:
            logger.error(f"Error running download for user {self.user.username}: {e}")
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "stats": self.stats
            }
    
    def download_specific_file(self, file_id: str) -> Dict[str, Any]:
        """
        Download a specific file by its ID.
        
        Args:
            file_id (str): Google Drive file ID
            
        Returns:
            Dict[str, Any]: Result of the download operation
        """
        try:
            logger.info(f"Downloading specific file {file_id} for user {self.user.username}")
            
            # Get file metadata
            file_metadata = self.drive_client.get_file_metadata(file_id)
            if not file_metadata:
                return {"success": False, "error": f"File not found: {file_id}"}
            
            # Download the file
            download_result = self.file_downloader.download(file_id, file_metadata)
            
            if download_result.get("success", False):
                self.stats["files_downloaded"] += 1
                
                # Delete from Drive if configured
                try:
                    if self.config.get("download", {}).get("delete_after_download", False) and not self.dry_run:
                        if self.drive_client.delete_file(file_id):
                            self.stats["files_deleted"] += 1
                            logger.info(f"Deleted file {file_id} from Google Drive after successful download")
                except Exception as delete_error:
                    logger.error(f"Error deleting file {file_id} after download: {delete_error}")
                    # Continue with other operations even if delete fails
                
                # Attempt transcription if needed
                if self.auto_transcribe and self.transcription_available:
                    if self.file_filter.should_transcribe(file_metadata["name"]):
                        self._transcribe_file(download_result["local_path"])
            
            return download_result
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            logger.debug(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def get_download_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a download job.
        
        Args:
            job_id (str): Download job ID
            
        Returns:
            Dict[str, Any]: Download job status
        """
        return self.file_downloader.get_download_status(job_id)
    
    def _process_folder(self, folder_name: str) -> Dict[str, Any]:
        """
        Process a specific folder in Google Drive.
        
        Args:
            folder_name (str): Name of the folder
            
        Returns:
            Dict[str, Any]: Stats for this folder
        """
        logger.info(f"Processing folder: {folder_name}")
        folder_stats = {
            "files_found": 0,
            "files_downloaded": 0,
            "files_deleted": 0,
            "files_transcribed": 0,
            "errors": 0
        }
        
        # Get folder ID
        folder_id = 'root' if folder_name.lower() == 'root' else self.drive_client.find_folder_by_name(folder_name)
        if not folder_id:
            logger.warning(f"Folder not found: {folder_name}")
            folder_stats["errors"] += 1
            return folder_stats
        
        # List files in the folder
        files = self.drive_client.list_files(folder_id)
        folder_stats["files_found"] = len(files)
        self.stats["files_found"] += len(files)
        
        # Filter files based on criteria
        download_files = self.file_filter.filter_files(files)
        
        # Process each file
        for file_metadata in download_files:
            file_id = file_metadata["id"]
            file_name = file_metadata["name"]
            
            try:
                # Download the file
                download_result = self.file_downloader.download(file_id, file_metadata)
                
                if download_result.get("success", False):
                    folder_stats["files_downloaded"] += 1
                    self.stats["files_downloaded"] += 1
                    
                    # Delete from Drive if configured
                    try:
                        if self.config.get("download", {}).get("delete_after_download", False) and not self.dry_run:
                            if self.drive_client.delete_file(file_id):
                                folder_stats["files_deleted"] += 1
                                self.stats["files_deleted"] += 1
                    except Exception as delete_error:
                        logger.error(f"Error processing file {file_name} delete_after_download: {delete_error}")
                        # Continue with other operations even if delete fails
                    
                    # Attempt transcription if needed
                    try:
                        if self.auto_transcribe and self.transcription_available:
                            if self.file_filter.should_transcribe(file_name):
                                transcription_result = self._transcribe_file(download_result["local_path"])
                                if transcription_result and transcription_result.get("success", False):
                                    folder_stats["files_transcribed"] += 1
                    except Exception as transcribe_error:
                        logger.error(f"Error transcribing file {file_name}: {transcribe_error}")
                        # Continue with other operations even if transcription fails
            
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {e}")
                logger.debug(traceback.format_exc())
                folder_stats["errors"] += 1
                self.stats["errors"] += 1
                # Continue with next file instead of stopping
        
        self.stats["folders_processed"] += 1
        return folder_stats
    
    def _transcribe_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Transcribe an audio file if transcription is available.
        
        Args:
            file_path (Path): Path to the audio file
            
        Returns:
            Optional[Dict[str, Any]]: Transcription result or None if failed/not available
        """
        if not self.transcription_available or not self.auto_transcribe:
            logger.debug(f"Transcription not available or disabled for user: {self.user.username}")
            return None
        
        try:
            # Ensure file_path is a Path object
            if isinstance(file_path, str):
                file_path = Path(file_path)
                
            logger.info(f"Transcribing file: {file_path}")
            transcription_service = TranscriptionManager(self.user_id, self.dry_run)
            
            # Create a transcription job record
            job = TranscriptionJob.objects.create(
                user=self.user,
                file_id=file_path.name,  # Use filename as ID since we don't have the Drive ID here
                file_name=file_path.name,
                status='processing',
                language=self.transcription_config.language or 'en',
                model=self.transcription_config.get_combined_config()['model']['name']
            )
            
            # Process the file
            result = transcription_service.transcribe_file(str(file_path))
            
            # Update the job record with results
            if result and result.get('success', False):
                job.status = 'completed'
                job.progress = 100
                job.completed_at = timezone.now()
                job.result_path = result.get('output_file')
                job.word_count = len(result.get('text', '').split())
                job.duration_seconds = result.get('duration', 0)
                job.save()
                
                logger.info(f"Transcription completed for {file_path.name}")
                self.stats["files_transcribed"] += 1
                return result
            else:
                # Handle failure
                error_msg = result.get('error', 'Unknown error during transcription') if result else 'Transcription failed'
                job.status = 'failed'
                job.error_message = error_msg
                job.save()
                
                logger.error(f"Transcription failed for {file_path.name}: {error_msg}")
                return None
            
        except Exception as e:
            logger.error(f"Error transcribing file {file_path}: {e}")
            logger.debug(traceback.format_exc())
            return None 