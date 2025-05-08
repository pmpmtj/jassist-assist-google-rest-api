"""
Django app configuration for classification functionality.
"""

from django.apps import AppConfig


class ClassificationConfig(AppConfig):
    """Django app configuration for classification app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jassist.web.classification'
    verbose_name = 'AI Content Classification'

    def ready(self):
        """
        Perform initialization when Django starts.
        """
        # Import signals to register them
        import jassist.web.classification.signals 