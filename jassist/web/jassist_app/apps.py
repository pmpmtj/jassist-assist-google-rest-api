from django.apps import AppConfig


class JassistAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jassist.web.jassist_app'
    verbose_name = 'JASSIST Core App'

    def ready(self):
        # Import signals if needed
        pass 