from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django_cryptography.fields import encrypt
import json
import logging

logger = logging.getLogger(__name__)

class GlobalDriveConfig(models.Model):
    """
    Global configuration for Google Drive downloads that applies to all users.
    Stores file types, download behavior, and timestamp settings.
    """
    include_extensions = ArrayField(models.CharField(max_length=20), default=list)
    delete_after_download = models.BooleanField(default=False)
    add_timestamp = models.BooleanField(default=True)
    timestamp_format = models.CharField(max_length=50, default='%Y%m%d_%H%M%S_%f')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Global Drive Configuration"
        verbose_name_plural = "Global Drive Configuration"
    
    def __str__(self):
        return f"Global Drive Config (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_config(cls):
        """Get the active global configuration or create a default one if none exists."""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'include_extensions': ['.m4a', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'],
                'delete_after_download': False,
                'add_timestamp': True,
                'timestamp_format': '%Y%m%d_%H%M%S_%f'
            }
        )
        if created:
            logger.info("Created default global drive configuration")
        return config


class UserDriveConfig(models.Model):
    """
    User-specific Google Drive download configuration.
    Stores target folders and scheduling preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='drive_config')
    target_folders = ArrayField(models.CharField(max_length=255), default=list)
    download_schedule = models.CharField(max_length=100, blank=True, null=True)  # cron format
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Drive Configuration"
        verbose_name_plural = "User Drive Configurations"
    
    def __str__(self):
        return f"Drive Config for {self.user.username}"
    
    def get_combined_config(self):
        """
        Combines global and user-specific configuration into a single dictionary.
        """
        global_config = GlobalDriveConfig.get_config()
        
        # Create the merged configuration structure
        config = {
            'file_types': {
                'include': global_config.include_extensions
            },
            'download': {
                'delete_after_download': global_config.delete_after_download,
                'add_timestamps': global_config.add_timestamp,
                'timestamp_format': global_config.timestamp_format
            },
            'folders': {
                'target_folders': self.target_folders
            },
            'user_id': self.user.id
        }
        
        return config


class DownloadRecord(models.Model):
    """
    Records of files downloaded from Google Drive.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='download_records')
    filename = models.CharField(max_length=255)
    source_id = models.CharField(max_length=100)  # Google Drive file ID
    source_folder = models.CharField(max_length=255)
    local_path = models.CharField(max_length=500)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    deleted_from_drive = models.BooleanField(default=False)
    file_size = models.BigIntegerField(default=0)  # Size in bytes
    
    class Meta:
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"{self.filename} - {self.user.username} ({self.downloaded_at.strftime('%Y-%m-%d')})"


class TranscriptionGlobalConfig(models.Model):
    """
    Global configuration for audio transcriptions that applies to all users.
    Only editable by administrators.
    """
    default_model = models.CharField(max_length=100, default="gpt-4o-transcribe")
    response_format = models.CharField(max_length=20, default="json", 
                          choices=[("json", "JSON"), ("text", "Plain Text"), ("srt", "SRT"), ("vtt", "VTT")])
    cost_management = models.JSONField(default=dict, blank=True, 
                                      help_text="Settings for maximum duration and other cost controls")
    default_prompt = models.TextField(blank=True, null=True, 
                                     help_text="System-wide default prompt for transcription")
    timestamp_format = models.CharField(max_length=50, default='%Y%m%d_%H%M%S_%f',
                                       help_text="Format for timestamping transcription files")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Global Transcription Configuration"
        verbose_name_plural = "Global Transcription Configuration"
    
    def __str__(self):
        return f"Global Transcription Config (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_config(cls):
        """Get the active global configuration or create a default one if none exists."""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'default_model': "gpt-4o-transcribe",
                'response_format': "json",
                'cost_management': {
                    'max_audio_duration_seconds': 300,
                    'warn_on_large_files': True
                },
                'timestamp_format': '%Y%m%d_%H%M%S_%f'
            }
        )
        if created:
            logger.info("Created default global transcription configuration")
        return config


class UserTranscriptionConfig(models.Model):
    """
    User-specific transcription configuration.
    Users can only modify their language preference; all other settings come from global config.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='transcription_config')
    api_key = encrypt(models.CharField(max_length=255, help_text="User's OpenAI API key (stored encrypted)"))
    language = models.CharField(max_length=50, blank=True, null=True, 
                               help_text="Preferred language code (e.g., 'en', 'fr', 'es')")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Transcription Configuration"
        verbose_name_plural = "User Transcription Configurations"
    
    def __str__(self):
        return f"Transcription Config for {self.user.username}"
    
    def get_combined_config(self):
        """
        Combines global and user-specific transcription configuration into a single dictionary.
        """
        global_config = TranscriptionGlobalConfig.get_config()
        
        # Create the merged configuration structure
        config = {
            'model': {
                'name': global_config.default_model,
                'language': self.language,  # User can customize language
                'prompt': global_config.default_prompt
            },
            'response_format': global_config.response_format,
            'cost_management': global_config.cost_management,
            'timestamp_format': global_config.timestamp_format,
            'user_id': self.user.id
        }
        
        return config

class TranscriptionJob(models.Model):
    """
    Represents a transcription job for audio files.
    Tracks the status and metadata of the transcription process.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transcription_jobs')
    file_id = models.CharField(max_length=255, help_text="Google Drive file ID")
    file_name = models.CharField(max_length=255, null=True, blank=True)
    download_record = models.ForeignKey('DownloadRecord', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='transcription_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    language = models.CharField(max_length=10, default='en-US')
    model = models.CharField(max_length=100, default='gpt-4o-transcribe')
    progress = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    
    # Results
    result_path = models.CharField(max_length=500, null=True, blank=True)
    result_format = models.CharField(max_length=20, default='json')
    word_count = models.IntegerField(default=0)
    duration_seconds = models.FloatField(default=0)
    transcript_content = models.TextField(null=True, blank=True, help_text="Full transcription content")
    transcript_summary = models.TextField(null=True, blank=True, help_text="Short summary of the transcription")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Transcription Job"
        verbose_name_plural = "Transcription Jobs"
    
    def __str__(self):
        return f"Job {self.id} - {self.file_name or self.file_id} ({self.status})"
    
    def update_status(self, status, error_message=None):
        """Update job status and related fields."""
        from django.utils import timezone
        
        self.status = status
        if status == 'completed':
            self.completed_at = timezone.now()
            self.progress = 100
        elif status == 'failed':
            self.error_message = error_message
        
        self.save(update_fields=['status', 'error_message', 'completed_at', 
                                'progress', 'updated_at'])
        
        logger.info(f"Transcription job {self.id} status updated to {status}")
        return self 