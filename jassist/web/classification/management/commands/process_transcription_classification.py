"""
Management command to process transcription classifications.

This command retrieves unprocessed transcription records, processes them through
the classification system, and updates the database with the results.
"""

import logging
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from jassist.web.download_gdrive.models import TranscriptionJob
from jassist.web.classification.classification_processor import batch_classify_transcriptions

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to process transcription classifications."""
    
    help = """
    Process transcription records through the classification system.
    
    Examples:
    
    # Process all unlabeled transcriptions (default)
    python manage.py process_transcription_classification
    
    # Process only a specific job
    python manage.py process_transcription_classification --job-id=123
    
    # Process with a dry run (no database updates)
    python manage.py process_transcription_classification --dry-run
    
    # Process all completed transcriptions (even if already labeled)
    python manage.py process_transcription_classification --force
    
    # Limit the number of records processed
    python manage.py process_transcription_classification --limit=50
    
    # Adjust batch size for processing
    python manage.py process_transcription_classification --batch-size=20
    """
    
    def add_arguments(self, parser):
        """Add command arguments."""
        # Single job mode
        parser.add_argument(
            '--job-id',
            type=int,
            help='Process only the specified job ID'
        )
        
        # Multiple job mode
        parser.add_argument(
            '--job-ids',
            nargs='+',
            type=int,
            help='List of job IDs to process'
        )
        
        # Processing options
        parser.add_argument(
            '--force',
            action='store_true',
            help='Process all completed jobs, even if already labeled'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without updating the database (for testing)'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of records to process'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=20,
            help='Number of records to process in a batch (default: 20)'
        )
    
    def handle(self, *args, **options):
        """Run the command."""
        try:
            # Parse options
            job_id = options.get('job_id')
            job_ids = options.get('job_ids', [])
            force = options.get('force', False)
            dry_run = options.get('dry_run', False)
            limit = options.get('limit')
            batch_size = options.get('batch_size', 20)
            
            # Job ID validation
            if job_id:
                job_ids = [job_id]
            
            # Create a combined job ID list
            combined_job_ids = job_ids if job_ids else None
            
            # Log the execution plan
            if dry_run:
                self.stdout.write("Running in DRY RUN mode - no database changes will be made")
            
            if combined_job_ids:
                self.stdout.write(f"Processing specific jobs: {combined_job_ids}")
                
                # Verify jobs exist before proceeding
                existing_ids = list(TranscriptionJob.objects.filter(
                    id__in=combined_job_ids
                ).values_list('id', flat=True))
                
                missing_ids = set(combined_job_ids) - set(existing_ids)
                if missing_ids:
                    self.stdout.write(
                        self.style.WARNING(f"Warning: Jobs not found: {missing_ids}")
                    )
                    # Continue with existing IDs only
                    combined_job_ids = existing_ids
                    if not combined_job_ids:
                        raise CommandError("No valid job IDs to process")
            else:
                count_query = TranscriptionJob.objects.filter(status='completed')
                if not force:
                    count_query = count_query.filter(content_label='unlabeled')
                
                total_jobs = count_query.count()
                jobs_to_process = min(limit, total_jobs) if limit else total_jobs
                
                self.stdout.write(
                    f"Processing {jobs_to_process} of {total_jobs} completed "
                    f"{'(unlabeled) ' if not force else ''}transcription jobs"
                )
            
            # Execute the classification process
            self.stdout.write("Starting classification process...")
            
            successful, processed = batch_classify_transcriptions(
                limit=limit,
                job_ids=combined_job_ids,
                force=force,
                dry_run=dry_run,
                batch_size=batch_size
            )
            
            # Report results
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"DRY RUN completed: {successful}/{processed} jobs would be successfully classified"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Classification completed: {successful}/{processed} jobs successfully classified"
                    )
                )
            
            # Return success
            return 0
            
        except Exception as e:
            logger.exception(f"Error executing process_transcription_classification: {e}")
            raise CommandError(f"Command failed: {e}") 