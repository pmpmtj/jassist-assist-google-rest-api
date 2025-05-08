"""
Transcription Manager module.

This module serves as the orchestration layer for the transcription process.
It coordinates the interactions between the audio preprocessing,
OpenAI client, result processing, and metrics collection.
"""
import logging
import traceback
from typing import Dict, Any, Optional, Union
from pathlib import Path

from django.contrib.auth.models import User
from django.conf import settings

from ...models import UserTranscriptionConfig
from .audio_preprocessor import AudioPreprocessor
from .openai_client import OpenAITranscriptionClient
from .result_processor import TranscriptionResultProcessor
from .metrics_collector import TranscriptionMetricsCollector

# Create a logger
logger = logging.getLogger(__name__)

class TranscriptionManager:
    """
    Orchestrates the transcription process for audio files.
    """
    def __init__(self, user_id: int, dry_run: bool = False):
        """
        Initialize the transcription manager for a specific user.
        
        Args:
            user_id (int): User ID
            dry_run (bool): If True, no actual transcriptions will occur
        """
        self.user_id = user_id
        self.dry_run = dry_run
        self.user = User.objects.get(id=user_id)
        self.stats = {
            "files_found": 0,
            "files_transcribed": 0,
            "errors": 0,
            "total_duration": 0
        }
        
        # Initialize user configuration
        self._initialize_user_config()
        
        # Initialize components
        self.audio_preprocessor = AudioPreprocessor()
        self.openai_client = OpenAITranscriptionClient(self.user_config.api_key)
        self.result_processor = TranscriptionResultProcessor(self.config)
        self.metrics_collector = TranscriptionMetricsCollector(self.user_id)
    
    def _initialize_user_config(self):
        """Initialize and validate user configuration."""
        try:
            self.user_config = UserTranscriptionConfig.objects.get(user_id=self.user_id)
            
            # Check if user has active configuration
            if not self.user_config.is_active:
                logger.warning(f"Transcription disabled for user: {self.user.username}")
                raise ValueError("Transcription is disabled for this user")
                
            # Combine global and user settings
            self.config = self.user_config.get_combined_config()
            
        except UserTranscriptionConfig.DoesNotExist:
            logger.error(f"No transcription configuration found for user: {self.user_id}")
            raise ValueError(f"No transcription configuration found for user: {self.user_id}")
        
        # Create user-specific directory for transcriptions
        self.base_transcription_dir = self._create_user_transcription_dir()
    
    def _create_user_transcription_dir(self) -> Path:
        """
        Create and return path to user's transcription directory.
        
        Returns:
            Path: Path to the user's transcription directory
        """
        import os
        # Base directory for all transcriptions
        transcription_base = Path(settings.BASE_DIR) / "media" / "transcriptions"
        
        # User-specific directory
        user_dir = transcription_base / str(self.user_id)
        
        # Create directories if they don't exist
        os.makedirs(user_dir, exist_ok=True)
        
        logger.debug(f"User transcription directory: {user_dir}")
        return user_dir
    
    def transcribe_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Transcribe a file using the OpenAI API.
        
        Args:
            file_path (Union[str, Path]): Path to the audio file
            
        Returns:
            Dict[str, Any]: Transcription result
        """
        try:
            # Ensure file_path is a Path object
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would transcribe file: {file_path}")
                return {"success": True, "text": "DRY RUN - No actual transcription performed"}
            
            logger.info(f"Beginning transcription for: {file_path.name}")
            self.stats["files_found"] += 1
            
            # Step 1: Validate and prepare audio
            validation_result = self.audio_preprocessor.validate_audio(file_path)
            if not validation_result["valid"]:
                logger.error(f"File validation failed: {validation_result.get('error')}")
                self.stats["errors"] += 1
                return {"success": False, "error": validation_result.get("error")}
            
            # Get audio duration if available
            duration = validation_result.get("duration")
            if duration:
                logger.info(f"Estimated duration: {duration:.2f} seconds")
                self.stats["total_duration"] += duration
                
                # Check cost management settings
                cost_config = self.config.get("cost_management", {})
                max_duration = cost_config.get("max_audio_duration_seconds", 300)
                warn_on_large = cost_config.get("warn_on_large_files", True)
                
                # Only warn if configured to do so
                if duration > max_duration and warn_on_large:
                    logger.warning(f"Audio exceeds max allowed ({max_duration}s). Proceeding with caution...")
                    
                # Record job start in metrics
                self.metrics_collector.record_transcription_job(
                    file_path.name, 
                    validation_result.get("file_size", 0),
                    duration, 
                    self.config.get("model", {}).get("name", "gpt-4o-transcribe")
                )
            
            # Step 2: Preprocess audio if needed
            if validation_result.get("needs_processing", False):
                logger.debug("Audio file needs preprocessing")
                processed_path = self.audio_preprocessor.prepare_audio(
                    file_path, 
                    output_format=validation_result.get("recommended_format", "mp3")
                )
                if processed_path is None:
                    logger.error("Audio preprocessing failed")
                    self.stats["errors"] += 1
                    return {"success": False, "error": "Audio preprocessing failed"}
                
                # Use processed file for transcription
                file_to_transcribe = processed_path
            else:
                file_to_transcribe = file_path
            
            # Step 3: Transcribe the file
            # Extract model configuration
            model_config = self.config.get("model", {})
            model_name = model_config.get("name", "gpt-4o-transcribe")
            language = model_config.get("language")
            prompt = model_config.get("prompt")
            response_format = self.config.get("response_format", "json")
            
            # Log configuration
            logger.debug(f"Using model: {model_name}")
            if prompt:
                logger.debug(f"Using prompt: {prompt}")
            if language:
                logger.debug(f"Using language: {language}")
            logger.debug(f"Using response format: {response_format}")
            
            # Send transcription request
            transcription_result = self.openai_client.transcribe(
                file_to_transcribe, 
                model=model_name,
                language=language,
                prompt=prompt,
                response_format=response_format
            )
            
            if not transcription_result or "error" in transcription_result:
                error_msg = transcription_result.get("error", "Unknown error in transcription")
                logger.error(f"Transcription failed: {error_msg}")
                self.stats["errors"] += 1
                return {"success": False, "error": error_msg}
            
            # Step 4: Process and save the result
            processed_result = self.result_processor.format_result(
                transcription_result, 
                output_format=self.config.get("output_format", "txt")
            )
            
            # Save the result
            output_file = self.result_processor.save_transcription(
                processed_result,
                file_path,
                self.base_transcription_dir
            )
            
            # Update metrics
            if duration:
                self.metrics_collector.update_job_completion(
                    file_path.name, 
                    success=True, 
                    result_size=len(processed_result.get("text", ""))
                )
            
            logger.info(f"Transcription completed successfully for {file_path.name}")
            self.stats["files_transcribed"] += 1
            
            return {
                "success": True,
                "text": processed_result.get("text", ""),
                "output_file": str(output_file),
                "duration": duration,
                "model": model_name
            }
            
        except Exception as e:
            logger.error(f"Error transcribing file {file_path}: {e}")
            logger.debug(traceback.format_exc())
            self.stats["errors"] += 1
            return {"success": False, "error": str(e)}
    
    def get_transcription_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a transcription job.
        
        Args:
            job_id (str): Transcription job ID
            
        Returns:
            Dict[str, Any]: Job status
        """
        # For now, transcription is synchronous, so this is a placeholder for future async processing
        return {"status": "not_found", "error": f"Job {job_id} not found"}
    
    def get_usage_stats(self, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get usage statistics for the user.
        
        Args:
            date_range (Optional[Dict[str, str]]): Date range filter (start_date, end_date)
            
        Returns:
            Dict[str, Any]: Usage statistics
        """
        return self.metrics_collector.generate_usage_report(date_range)
