"""
Signal handlers for classification models.
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings

from jassist.web.download_gdrive.models import TranscriptionJob
from .models import ClassificationPrompt, ClassificationConfig

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ClassificationConfig)
def config_saved(sender, instance, created, **kwargs):
    """Log when a classification configuration is saved."""
    if created:
        logger.info(f"Created classification config: {instance.assistant_name}")
    else:
        logger.debug(f"Updated classification config: {instance.assistant_name}")


@receiver(post_save, sender=ClassificationPrompt)
def prompt_saved(sender, instance, created, **kwargs):
    """Log when a classification prompt is saved."""
    if created:
        logger.info(f"Created classification prompt: {instance.name}")
    else:
        logger.debug(f"Updated classification prompt: {instance.name}")


# Optional: Uncomment this if you want to track when TranscriptionJob content_label is updated
"""
@receiver(post_save, sender=TranscriptionJob)
def track_classification_updates(sender, instance, created, **kwargs):
    # Only interested in updates to existing records, not creation
    if not created and 'update_fields' in kwargs and kwargs['update_fields']:
        # Check if content_label was one of the updated fields
        if 'content_label' in kwargs['update_fields']:
            logger.info(f"Transcription job {instance.id} classified as '{instance.content_label}'")
""" 