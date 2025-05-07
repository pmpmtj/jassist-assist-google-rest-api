"""
Django management command to run scheduled Google Drive downloads.
"""
import logging
import datetime
import croniter
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from download_gdrive.models import UserDriveConfig
from download_gdrive.services.download.download_manager import DownloadManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run scheduled Google Drive downloads for all users who have a download schedule'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force-all', 
            action='store_true',
            help='Run downloads for all users regardless of schedule'
        )
        parser.add_argument(
            '--user', 
            type=int,
            help='Run downloads for a specific user ID'
        )
    
    def handle(self, *args, **options):
        force_all = options.get('force_all', False)
        specific_user_id = options.get('user')
        
        try:
            # Get configurations that should be run
            if specific_user_id:
                configs = UserDriveConfig.objects.filter(user_id=specific_user_id, is_active=True)
                if not configs.exists():
                    self.stdout.write(self.style.ERROR(f"No active configuration found for user ID {specific_user_id}"))
                    return
            else:
                configs = UserDriveConfig.objects.filter(is_active=True)
                
            self.stdout.write(f"Found {configs.count()} active user configurations")
            
            # Process each config
            for config in configs:
                if self._should_run(config) or force_all:
                    self.stdout.write(f"Running download for user: {config.user.username}")
                    try:
                        downloader = DownloadManager(config.user.id)
                        result = downloader.run_downloads()
                        
                        if result.get('success', False):
                            stats = result.get('stats', {})
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Download successful for {config.user.username}. "
                                    f"Downloaded {stats.get('files_downloaded', 0)} files."
                                )
                            )
                        else:
                            error = result.get('error', 'Unknown error')
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Download failed for {config.user.username}: {error}"
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing download for {config.user.username}: {e}")
                        )
                else:
                    self.stdout.write(f"Skipping user {config.user.username} - not scheduled for now")
            
            self.stdout.write(self.style.SUCCESS("Scheduled downloads processing completed"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error running scheduled downloads: {e}"))
    
    def _should_run(self, config):
        """
        Determine if a download should run based on its schedule.
        
        Args:
            config: UserDriveConfig instance
            
        Returns:
            bool: True if the download should run now
        """
        # If no schedule is set, don't run automatically
        if not config.download_schedule:
            return False
            
        # If it's never been run, run it
        if not config.last_run:
            return True
        
        try:
            # Use croniter to determine if it's time to run based on the schedule
            cron = croniter.croniter(config.download_schedule, config.last_run)
            next_run = cron.get_next(datetime.datetime)
            
            # Convert to timezone-aware datetime if needed
            if timezone.is_naive(next_run):
                next_run = timezone.make_aware(next_run)
                
            # Check if the next run time is in the past
            return next_run <= timezone.now()
            
        except Exception as e:
            logger.error(f"Error parsing cron schedule for user {config.user.username}: {e}")
            return False 