"""
Classification Processor

Main module for classifying text into different categories using OpenAI Assistants.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Union, List, Tuple
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from jassist.web.download_gdrive.models import TranscriptionJob
from .models import TranscriptionClassificationBatch, ClassificationMetrics
from .classification_adapter import ClassificationAdapter, ClassificationError

logger = logging.getLogger(__name__)


class ClassificationProcessor:
    """
    Processor for classifying text using the OpenAI Assistant API.
    """
    
    def __init__(self):
        """
        Initialize the classification processor.
        """
        self.adapter = ClassificationAdapter()
        logger.debug("ClassificationProcessor initialized")
    
    def process_transcription_job(self, job: TranscriptionJob, dry_run: bool = False,
                                batch: Optional[TranscriptionClassificationBatch] = None) -> bool:
        """
        Process a single transcription job by classifying its content.
        
        Args:
            job: The TranscriptionJob to process
            dry_run: If True, don't actually update the database
            batch: Optional batch to update metrics
            
        Returns:
            bool: True if successful, False otherwise
        """
        job_id = job.id
        start_time = time.time()
        
        logger.info(f"Processing transcription job {job_id}: '{job.file_name}'")
        
        try:
            # Skip if no content to classify
            if not job.transcript_content:
                logger.warning(f"Job {job_id} has no transcript content to classify")
                return False
            
            # Classify the text
            batch_id = batch.batch_id if batch else None
            
            # Create the input with all relevant context
            input_data = {
                "transcript_content": job.transcript_content,
                "job_id": job_id,
                "file_name": job.file_name,
                "language": job.language
            }
            
            # Get the classification result
            result = self.adapter.classify_text(
                input_data, 
                job_id=job_id,
                batch_id=batch_id
            )
            
            if not result:
                logger.error(f"Empty classification result for job {job_id}")
                return False
            
            # Parse the classification result and update the job
            success = self._update_job_classification(job, result, dry_run)
            
            # Log classification completion
            elapsed_time = time.time() - start_time
            if success:
                logger.info(f"Classification successful for job {job_id} in {elapsed_time:.2f}s")
                if batch:
                    # Update batch metrics with success
                    batch.update_metrics(processed=1, successful=1, failed=0)
            else:
                logger.error(f"Failed to update classification for job {job_id}")
                if batch:
                    # Update batch metrics with failure
                    batch.update_metrics(processed=1, successful=0, failed=1)
            
            return success
            
        except ClassificationError as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Classification error for job {job_id}: {e} (after {elapsed_time:.2f}s)")
            
            if batch:
                # Update batch metrics with failure
                batch.update_metrics(processed=1, successful=0, failed=1)
            
            return False
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.exception(f"Unexpected error processing job {job_id}: {e} (after {elapsed_time:.2f}s)")
            
            if batch:
                # Update batch metrics with failure
                batch.update_metrics(processed=1, successful=0, failed=1)
            
            return False
    
    def _update_job_classification(self, job: TranscriptionJob, result: str, dry_run: bool) -> bool:
        """
        Update the job with the classification result.
        
        Args:
            job: The TranscriptionJob to update
            result: The classification result from the adapter
            dry_run: If True, don't actually update the database
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try to parse the result as JSON first
            try:
                classification_data = json.loads(result)
                
                # Look for classifications array in the response
                if "classifications" in classification_data and classification_data["classifications"]:
                    # Get the first classification (or the most prominent one)
                    classifications = classification_data["classifications"]
                    
                    # Find the first valid classification with a known category
                    valid_categories = dict(TranscriptionJob.CONTENT_LABEL_CHOICES)
                    
                    # Find first match or fallback to the first classification
                    content_label = "unlabeled"
                    found_classification = False
                    
                    for classification in classifications:
                        if "category" in classification:
                            category = classification["category"].lower()
                            
                            # Map some common categories to our system categories
                            category_mapping = {
                                "diario": "diary",
                                "agenda": "calendar",
                                "tarefas": "todo",
                                "contas": "other",
                                "contactos": "other",
                                "entidades": "other",
                                # English mappings
                                "task": "todo",
                                "tasks": "todo",
                                "diary": "diary",
                                "journal": "diary",
                                "calendar": "calendar",
                                "appointment": "calendar",
                                "meeting": "meeting",
                                "contacts": "other",
                                "accounts": "other",
                                "note": "note",
                                "notes": "note"
                            }
                            
                            # Try to map the category
                            if category in category_mapping:
                                mapped_category = category_mapping[category]
                                if mapped_category in valid_categories:
                                    content_label = mapped_category
                                    found_classification = True
                                    break
                            
                            # Direct match with our system categories
                            if category in valid_categories:
                                content_label = category
                                found_classification = True
                                break
                    
                    if not found_classification and classifications:
                        # Just use the first classification's category if nothing matched
                        logger.warning(
                            f"No valid category found in classifications. "
                            f"Using 'unlabeled' for job {job.id}"
                        )
                
                elif "category" in classification_data:
                    # Simple format with just a category field
                    category = classification_data["category"].lower()
                    valid_categories = dict(TranscriptionJob.CONTENT_LABEL_CHOICES)
                    if category in valid_categories:
                        content_label = category
                    else:
                        logger.warning(
                            f"Unknown category '{category}' in classification result for job {job.id}. "
                            f"Using 'unlabeled'"
                        )
                        content_label = "unlabeled"
                
                else:
                    # No recognized format, use a text search approach
                    logger.warning(
                        f"Unexpected classification format for job {job.id}. "
                        f"Will attempt text-based category extraction."
                    )
                    content_label = self._extract_category_from_text(result)
            
            except json.JSONDecodeError:
                # Not valid JSON, try to extract category using text search
                logger.warning(
                    f"Classification result for job {job.id} is not valid JSON. "
                    f"Will attempt text-based category extraction."
                )
                content_label = self._extract_category_from_text(result)
            
            # Update the job if not a dry run
            if not dry_run:
                with transaction.atomic():
                    job.content_label = content_label
                    job.save(update_fields=['content_label', 'updated_at'])
                    logger.info(f"Updated job {job.id} with classification: {content_label}")
            else:
                logger.info(f"Dry run: Would update job {job.id} with classification: {content_label}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error parsing classification result for job {job.id}: {e}", exc_info=True)
            return False
    
    def _extract_category_from_text(self, text: str) -> str:
        """
        Extract a category from text using simple pattern matching.
        
        Args:
            text: The text to extract category from
            
        Returns:
            str: The extracted category or 'unlabeled' if none found
        """
        text = text.lower()
        
        # Define category keywords
        category_keywords = {
            "diary": ["diary", "journal", "diario"],
            "calendar": ["calendar", "agenda", "appointment", "schedule"],
            "meeting": ["meeting", "reunion", "conference"],
            "note": ["note", "notes", "reminder"],
            "todo": ["todo", "task", "tasks", "to-do", "to do", "tarefas"],
            "other": ["other", "contact", "account", "miscellaneous"]
        }
        
        # Search for keywords
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        # Default fallback
        return "unlabeled"
    
    def batch_process_transcriptions(self, limit: Optional[int] = None, job_ids: Optional[List[int]] = None,
                                   force: bool = False, dry_run: bool = False,
                                   batch_size: int = 20) -> Tuple[int, int]:
        """
        Process multiple transcription jobs in a batch.
        
        Args:
            limit: Optional maximum number of jobs to process
            job_ids: Optional list of specific job IDs to process
            force: If True, process all completed jobs, even if already labeled
            dry_run: If True, don't actually update the database
            batch_size: Number of jobs to process in a single batch
            
        Returns:
            Tuple[int, int]: (number of successful jobs, total jobs processed)
        """
        # Create a batch record
        batch = TranscriptionClassificationBatch.objects.create(
            dry_run=dry_run
        )
        
        try:
            # Start batch processing
            batch.start_processing()
            
            # Build the query
            query = TranscriptionJob.objects.filter(status='completed')
            
            if not force:
                # Only process unlabeled transcriptions
                query = query.filter(content_label='unlabeled')
            
            if job_ids:
                # Filter by specific job IDs
                query = query.filter(id__in=job_ids)
            
            # Get total number of jobs to process
            total_jobs = query.count()
            limit = min(limit, total_jobs) if limit else total_jobs
            batch.total_records = limit
            batch.save(update_fields=['total_records'])
            
            logger.info(f"Starting batch {batch.batch_id}: {limit} jobs to process")
            
            # Process jobs in batches
            processed = 0
            successful = 0
            
            for i in range(0, limit, batch_size):
                # Get a batch of jobs
                batch_jobs = query.order_by('id')[i:i+batch_size]
                
                for job in batch_jobs:
                    # Process the job
                    success = self.process_transcription_job(job, dry_run, batch)
                    
                    processed += 1
                    if success:
                        successful += 1
                    
                    # Log progress
                    if processed % 10 == 0 or processed == limit:
                        logger.info(f"Processed {processed}/{limit} jobs ({successful} successful)")
                
                # Commit the batch metrics
                batch.save()
            
            # Complete the batch
            batch.complete_processing()
            
            logger.info(
                f"Batch {batch.batch_id} completed: "
                f"{successful}/{processed} jobs successfully processed"
            )
            
            return successful, processed
            
        except Exception as e:
            logger.exception(f"Error in batch processing: {e}")
            
            # Mark batch as failed
            batch.fail_processing(str(e))
            
            # Get current stats
            metrics = ClassificationMetrics.objects.filter(batch_id=batch.batch_id)
            processed = metrics.count()
            successful = metrics.filter(success=True).count()
            
            return successful, processed


def classify_transcription(job_id: int, dry_run: bool = False) -> bool:
    """
    Classify a single transcription job.
    
    Args:
        job_id: ID of the TranscriptionJob to process
        dry_run: If True, don't actually update the database
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        processor = ClassificationProcessor()
        
        # Get the job
        try:
            job = TranscriptionJob.objects.get(id=job_id)
        except TranscriptionJob.DoesNotExist:
            logger.error(f"TranscriptionJob with ID {job_id} not found")
            return False
        
        # Process the job
        return processor.process_transcription_job(job, dry_run)
        
    except Exception as e:
        logger.exception(f"Error classifying transcription {job_id}: {e}")
        return False


def batch_classify_transcriptions(limit: Optional[int] = None, job_ids: Optional[List[int]] = None,
                                force: bool = False, dry_run: bool = False,
                                batch_size: int = 20) -> Tuple[int, int]:
    """
    Classify multiple transcription jobs in a batch.
    
    Args:
        limit: Optional maximum number of jobs to process
        job_ids: Optional list of specific job IDs to process
        force: If True, process all completed jobs, even if already labeled
        dry_run: If True, don't actually update the database
        batch_size: Number of jobs to process in a single batch
        
    Returns:
        Tuple[int, int]: (number of successful jobs, total jobs processed)
    """
    try:
        processor = ClassificationProcessor()
        return processor.batch_process_transcriptions(
            limit=limit,
            job_ids=job_ids,
            force=force,
            dry_run=dry_run,
            batch_size=batch_size
        )
        
    except Exception as e:
        logger.exception(f"Error in batch classification: {e}")
        return 0, 0 