"""
Command to reset user transcription configurations.
This can be used to handle data migration issues when encryption is enabled.
"""
import logging
from django.core.management.base import BaseCommand
from download_gdrive.models import UserTranscriptionConfig

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resets all user transcription configurations'

    def handle(self, *args, **options):
        # Get all configurations first
        configs = list(UserTranscriptionConfig.objects.all())
        user_configs = {config.user_id: {'api_key': config.api_key, 'language': config.language} 
                       for config in configs}
        count = len(configs)
        
        # Delete all configurations
        UserTranscriptionConfig.objects.all().delete()
        
        # Report results
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} transcription configurations'))
        
        # Recreate configurations if needed
        if options.get('recreate', False):
            recreated = 0
            for user_id, data in user_configs.items():
                try:
                    UserTranscriptionConfig.objects.create(
                        user_id=user_id,
                        api_key=data['api_key'],
                        language=data['language'],
                        is_active=True
                    )
                    recreated += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to recreate config for user {user_id}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Successfully recreated {recreated} configurations'))
        
        logger.info(f"Reset {count} user transcription configurations") 