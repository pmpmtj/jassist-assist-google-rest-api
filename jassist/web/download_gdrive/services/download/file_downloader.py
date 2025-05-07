"""
File Downloader module.

This module handles the actual downloading of files from Google Drive
and manages the download process, including progress tracking.
"""
import logging
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
import traceback

from .google_drive_client import GoogleDriveClient
from .file_system_handler import FileSystemHandler
from ...models import DownloadRecord

# Create a logger
logger = logging.getLogger(__name__)

class FileDownloader:
    """
    Manages the download process for files from Google Drive.
    """
    def __init__(self, drive_client: GoogleDriveClient, file_system: FileSystemHandler, dry_run: bool = False):
        """
        Initialize the file downloader.
        
        Args:
            drive_client (GoogleDriveClient): Google Drive client
            file_system (FileSystemHandler): File system handler
            dry_run (bool): If True, no actual downloads will occur
        """
        self.drive_client = drive_client
        self.file_system = file_system
        self.dry_run = dry_run
        self.active_downloads = {}  # job_id -> status dict
        
    def download(self, file_id: str, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download a file from Google Drive.
        
        Args:
            file_id (str): Google Drive file ID
            file_metadata (Dict[str, Any]): File metadata from Google Drive
            
        Returns:
            Dict[str, Any]: Result of the download operation
        """
        file_name = file_metadata.get('name', f"file_{file_id}")
        logger.info(f"Downloading file: {file_name} ({file_id})")
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would download {file_name}")
            return {"success": True, "file_id": file_id, "file_name": file_name, "dry_run": True}
        
        try:
            # Download the file content
            file_content = self.drive_client.download_file(file_id)
            
            if not file_content:
                logger.error(f"Failed to download content for file {file_name}")
                return {"success": False, "error": "Failed to download file content"}
            
            # Determine the local path where the file will be saved
            local_path = self.file_system.get_download_path(file_name)
            
            # Save the file
            self.file_system.save_file(local_path, file_content)
            
            # Get the file size
            file_size = len(file_content) if file_content else 0
            
            # Create a download record in the database
            record = DownloadRecord.objects.create(
                user=self.drive_client.user,
                filename=file_name,
                source_id=file_id,
                source_folder=file_metadata.get('parents', ['unknown'])[0] if 'parents' in file_metadata else 'unknown',
                local_path=str(local_path),
                file_size=file_size
            )
            
            logger.info(f"Downloaded {file_name} to {local_path}")
            
            # Return success with file information
            return {
                "success": True,
                "file_id": file_id,
                "file_name": file_name,
                "local_path": str(local_path),
                "file_size": file_size,
                "download_id": str(record.id)
            }
            
        except Exception as e:
            logger.error(f"Error downloading file {file_name}: {e}")
            logger.debug(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def get_download_status(self, download_id: str) -> Dict[str, Any]:
        """
        Get the status of a download job.
        
        Args:
            download_id (str): Download record ID
            
        Returns:
            Dict[str, Any]: Download status
        """
        try:
            # Get the download record from the database
            from ....models import DownloadRecord
            
            try:
                record = DownloadRecord.objects.get(id=download_id)
                
                # Format the response
                return {
                    "success": True,
                    "status": "completed",  # Downloads are synchronous for now
                    "file_id": record.source_id,
                    "file_name": record.filename,
                    "local_path": record.local_path,
                    "file_size": record.file_size,
                    "downloaded_at": record.downloaded_at.isoformat(),
                }
                
            except DownloadRecord.DoesNotExist:
                logger.warning(f"Download record not found: {download_id}")
                return {
                    "success": False,
                    "error": f"Download record not found: {download_id}"
                }
                
        except Exception as e:
            logger.error(f"Error getting download status: {e}")
            logger.debug(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_download(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel an active download job.
        
        Args:
            job_id (str): Download job ID
            
        Returns:
            Dict[str, Any]: Result of the cancel operation
        """
        if job_id not in self.active_downloads:
            return {"success": False, "error": f"Job {job_id} not found"}
        
        status = self.active_downloads[job_id]["status"]
        if status == "completed" or status == "failed":
            return {
                "success": False, 
                "error": f"Cannot cancel job in {status} state"
            }
        
        self.active_downloads[job_id]["status"] = "cancelled"
        logger.info(f"Cancelled download job {job_id}")
        
        return {"success": True, "message": f"Job {job_id} cancelled"}
    
    def _record_download(self, file_id: str, filename: str, file_size: int, local_path: Path) -> None:
        """
        Record a successful download in the database.
        
        Args:
            file_id (str): Google Drive file ID
            filename (str): Original file name
            file_size (int): File size in bytes
            local_path (Path): Local path where the file was saved
        """
        try:
            # Create a record in the database
            record = DownloadRecord(
                user_id=self.file_system.user_id,
                filename=filename,
                source_id=file_id,
                local_path=str(local_path),
                file_size=file_size,
            )
            record.save()
            logger.debug(f"Recorded download for {filename} in database")
            
        except Exception as e:
            logger.error(f"Failed to record download in database: {e}", exc_info=True) 