"""
Unit tests for download_gdrive models.
"""
import logging
from django.test import TestCase
from django.contrib.auth.models import User
from jassist.web.download_gdrive.models import (
    GlobalDriveConfig,
    UserDriveConfig,
    DownloadRecord,
    TranscriptionGlobalConfig,
    UserTranscriptionConfig,
    TranscriptionJob
)

logger = logging.getLogger(__name__)


class GlobalDriveConfigTest(TestCase):
    """Test cases for GlobalDriveConfig model."""
    
    def setUp(self):
        """Set up test environment."""
        logger.debug("Setting up GlobalDriveConfigTest")
        # The model automatically creates a default instance when get_config is called
        self.config = GlobalDriveConfig.get_config()
    
    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        self.assertEqual(GlobalDriveConfig.objects.count(), 1)
        self.assertIn('.pdf', self.config.include_extensions)
        self.assertFalse(self.config.delete_after_download)
        self.assertTrue(self.config.add_timestamp)
        self.assertEqual(self.config.timestamp_format, '%Y%m%d_%H%M%S_%f')


class UserDriveConfigTest(TestCase):
    """Test cases for UserDriveConfig model."""
    
    def setUp(self):
        """Set up test environment."""
        logger.debug("Setting up UserDriveConfigTest")
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.config = UserDriveConfig.objects.create(
            user=self.user,
            target_folders=['/path/to/folder1', '/path/to/folder2'],
            download_schedule='0 0 * * *',  # Run at midnight every day
            is_active=True
        )
    
    def test_user_config_creation(self):
        """Test that user configuration is created properly."""
        self.assertEqual(UserDriveConfig.objects.count(), 1)
        self.assertEqual(self.config.user, self.user)
        self.assertEqual(len(self.config.target_folders), 2)
        self.assertEqual(self.config.download_schedule, '0 0 * * *')
        self.assertTrue(self.config.is_active)
    
    def test_get_combined_config(self):
        """Test that combined configuration is generated correctly."""
        # Ensure GlobalDriveConfig exists
        global_config = GlobalDriveConfig.get_config()
        
        combined = self.config.get_combined_config()
        self.assertEqual(combined['user_id'], self.user.id)
        self.assertEqual(combined['folders']['target_folders'], self.config.target_folders)
        self.assertEqual(combined['file_types']['include'], global_config.include_extensions)


class TranscriptionGlobalConfigTest(TestCase):
    """Test cases for TranscriptionGlobalConfig model."""
    
    def setUp(self):
        """Set up test environment."""
        logger.debug("Setting up TranscriptionGlobalConfigTest")
        self.config = TranscriptionGlobalConfig.get_config()
    
    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        self.assertEqual(TranscriptionGlobalConfig.objects.count(), 1)
        self.assertEqual(self.config.default_model, "whisper-1")
        self.assertEqual(self.config.response_format, "json")
        self.assertIn('max_audio_duration_seconds', self.config.cost_management) 