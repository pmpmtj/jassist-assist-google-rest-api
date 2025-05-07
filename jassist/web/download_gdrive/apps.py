from django.apps import AppConfig


class DownloadGdriveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jassist.web.download_gdrive'
    verbose_name = 'Google Drive Download'

    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        """
        # Import signals if we have any
        try:
            import jassist.web.download_gdrive.signals  # noqa
        except ImportError:
            # No signals module, that's okay
            pass 