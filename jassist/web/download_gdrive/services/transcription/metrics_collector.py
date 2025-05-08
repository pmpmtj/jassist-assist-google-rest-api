"""
Transcription Metrics Collector module.

This module handles tracking usage and performance metrics for transcription.
"""
import json
import logging
import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from django.utils import timezone
from django.conf import settings

# Create a logger
logger = logging.getLogger(__name__)

class TranscriptionMetricsCollector:
    """
    Tracks usage and performance metrics for transcription.
    """
    def __init__(self, user_id: int):
        """
        Initialize the metrics collector.
        
        Args:
            user_id (int): User ID
        """
        self.user_id = user_id
        self.metrics_dir = self._initialize_metrics_dir()
        self.active_jobs = {}  # job_id -> job metadata
    
    def _initialize_metrics_dir(self) -> Path:
        """
        Initialize metrics directory.
        
        Returns:
            Path: Path to the metrics directory
        """
        import os
        # Base metrics directory
        metrics_base = Path(settings.BASE_DIR) / "logs" / "transcription_metrics"
        
        # User-specific directory
        user_dir = metrics_base / str(self.user_id)
        
        # Create directories if they don't exist
        os.makedirs(user_dir, exist_ok=True)
        
        return user_dir
    
    def record_transcription_job(
        self, 
        file_name: str,
        file_size: int,
        duration: Optional[float] = None,
        model: str = "gpt-4o-transcribe"
    ) -> Dict[str, Any]:
        """
        Record the start of a transcription job.
        
        Args:
            file_name (str): Name of the file being transcribed
            file_size (int): Size of the file in bytes
            duration (Optional[float]): Duration of the audio in seconds
            model (str): Model being used
            
        Returns:
            Dict[str, Any]: Job metadata
        """
        # Generate a job ID
        job_id = f"job_{timezone.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
        
        # Create job metadata
        job_data = {
            "job_id": job_id,
            "user_id": self.user_id,
            "file_name": file_name,
            "file_size": file_size,
            "duration": duration,
            "model": model,
            "start_time": timezone.now().isoformat(),
            "status": "started",
            "completion_time": None,
            "processing_time": None,
            "success": None,
            "result_size": None,
            "estimated_cost": self._calculate_cost(duration, model) if duration else None
        }
        
        # Store in active jobs
        self.active_jobs[job_id] = job_data
        
        # Log job start
        self._log_event("job_start", job_data)
        
        return job_data
    
    def update_job_completion(
        self,
        file_name: str, 
        success: bool = True, 
        result_size: Optional[int] = None, 
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update job completion status.
        
        Args:
            file_name (str): Name of the file (to match with active job)
            success (bool): Whether transcription was successful
            result_size (Optional[int]): Size of the result text
            error (Optional[str]): Error message if failed
            
        Returns:
            Optional[Dict[str, Any]]: Updated job metadata
        """
        # Find job by file name
        job_id = None
        for jid, job_data in self.active_jobs.items():
            if job_data.get("file_name") == file_name:
                job_id = jid
                break
        
        if not job_id:
            logger.warning(f"No active job found for file: {file_name}")
            return None
        
        # Update job data
        job_data = self.active_jobs[job_id]
        job_data["completion_time"] = timezone.now().isoformat()
        job_data["status"] = "completed" if success else "failed"
        job_data["success"] = success
        
        # Calculate processing time
        if "start_time" in job_data:
            try:
                start_time = datetime.datetime.fromisoformat(job_data["start_time"])
                completion_time = datetime.datetime.fromisoformat(job_data["completion_time"])
                processing_time = (completion_time - start_time).total_seconds()
                job_data["processing_time"] = processing_time
            except Exception as e:
                logger.error(f"Error calculating processing time: {e}")
        
        # Add result metadata
        if result_size is not None:
            job_data["result_size"] = result_size
        
        if error:
            job_data["error"] = error
        
        # Log job completion
        self._log_event("job_completion", job_data)
        
        return job_data
    
    def _calculate_cost(self, duration: Optional[float], model: str = "gpt-4o-transcribe") -> Dict[str, Any]:
        """
        Calculate the estimated cost of a transcription job.
        
        Args:
            duration (Optional[float]): Duration of audio in seconds
            model (str): Model name
            
        Returns:
            Dict[str, Any]: Cost estimate
        """
        if duration is None:
            return {"estimated_cost_usd": 0}
        
        # Current OpenAI pricing (as of 2023, subject to change)
        pricing = {
            "gpt-4o-transcribe": 0.006  # $0.006 per minute
        }
        
        # Default to gpt-4o-transcribe pricing if model not found
        per_minute_cost = pricing.get(model, pricing["gpt-4o-transcribe"])
        
        # Convert seconds to minutes and calculate cost
        duration_minutes = duration / 60.0
        estimated_cost = duration_minutes * per_minute_cost
        
        return {
            "duration_seconds": duration,
            "duration_minutes": duration_minutes,
            "model": model,
            "per_minute_cost": per_minute_cost,
            "estimated_cost_usd": estimated_cost
        }
    
    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log a metrics event.
        
        Args:
            event_type (str): Type of event
            data (Dict[str, Any]): Event data
        """
        try:
            # Create event log with timestamp
            event_log = {
                "timestamp": timezone.now().isoformat(),
                "event_type": event_type,
                "user_id": self.user_id,
                "data": data
            }
            
            # Get current month and year for file organization
            current_date = timezone.now().strftime("%Y%m")
            log_file = self.metrics_dir / f"transcription_metrics_{current_date}.jsonl"
            
            # Append to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_log) + "\n")
                
        except Exception as e:
            logger.error(f"Error logging transcription metric: {e}")
    
    def generate_usage_report(
        self, 
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate usage statistics for the user.
        
        Args:
            date_range (Optional[Dict[str, str]]): Date range filter (start_date, end_date)
            
        Returns:
            Dict[str, Any]: Usage statistics
        """
        try:
            # Initialize stats
            stats = {
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0,
                "total_duration_seconds": 0,
                "total_audio_files": 0,
                "total_processing_time": 0,
                "average_processing_time": 0,
                "estimated_total_cost": 0,
                "jobs_by_model": {},
                "jobs_by_day": {}
            }
            
            # Parse date range if provided
            start_date = None
            end_date = None
            
            if date_range:
                try:
                    if "start_date" in date_range:
                        start_date = datetime.datetime.fromisoformat(date_range["start_date"])
                    if "end_date" in date_range:
                        end_date = datetime.datetime.fromisoformat(date_range["end_date"])
                except Exception as e:
                    logger.error(f"Error parsing date range: {e}")
            
            # Default to current month if no range provided
            if not start_date and not end_date:
                today = timezone.now()
                start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Find log files in the metrics directory
            log_files = list(self.metrics_dir.glob("transcription_metrics_*.jsonl"))
            
            # Process each log file
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            event = json.loads(line)
                            
                            # Filter for job completion events
                            if event.get("event_type") != "job_completion":
                                continue
                            
                            # Extract job data
                            job_data = event.get("data", {})
                            
                            # Filter by date if needed
                            event_timestamp = job_data.get("completion_time")
                            if not event_timestamp:
                                continue
                                
                            try:
                                event_date = datetime.datetime.fromisoformat(event_timestamp)
                                
                                if start_date and event_date < start_date:
                                    continue
                                if end_date and event_date > end_date:
                                    continue
                                    
                            except Exception:
                                continue
                            
                            # Count job
                            stats["total_jobs"] += 1
                            
                            # Success/failure count
                            if job_data.get("success", False):
                                stats["successful_jobs"] += 1
                            else:
                                stats["failed_jobs"] += 1
                            
                            # Add duration if available
                            if job_data.get("duration"):
                                stats["total_duration_seconds"] += job_data["duration"]
                                stats["total_audio_files"] += 1
                            
                            # Add processing time if available
                            if job_data.get("processing_time"):
                                stats["total_processing_time"] += job_data["processing_time"]
                            
                            # Add cost if available
                            cost_data = job_data.get("estimated_cost", {})
                            if cost_data and "estimated_cost_usd" in cost_data:
                                stats["estimated_total_cost"] += cost_data["estimated_cost_usd"]
                            
                            # Count by model
                            model = job_data.get("model", "unknown")
                            if model not in stats["jobs_by_model"]:
                                stats["jobs_by_model"][model] = 0
                            stats["jobs_by_model"][model] += 1
                            
                            # Count by day
                            job_date_str = event_date.strftime("%Y-%m-%d")
                            if job_date_str not in stats["jobs_by_day"]:
                                stats["jobs_by_day"][job_date_str] = 0
                            stats["jobs_by_day"][job_date_str] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing log file {log_file}: {e}")
            
            # Calculate averages
            if stats["successful_jobs"] > 0:
                stats["average_processing_time"] = stats["total_processing_time"] / stats["successful_jobs"]
            
            # Add date range to stats
            stats["date_range"] = {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating usage report: {e}")
            return {
                "error": str(e),
                "total_jobs": 0,
                "successful_jobs": 0,
                "failed_jobs": 0
            }
