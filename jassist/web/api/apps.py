from django.apps import AppConfig
import logging

logger = logging.getLogger('api')


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jassist.web.api'
    verbose_name = 'API'

    def ready(self):
        """
        Perform initialization tasks when the API app is ready.
        """
        print("INFO", self.name, "API layer initialized")
        # Import signals or perform other startup tasks if needed
        pass 