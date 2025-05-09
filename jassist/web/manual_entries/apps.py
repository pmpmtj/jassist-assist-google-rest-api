from django.apps import AppConfig


class ManualEntriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jassist.web.manual_entries'
    label = 'manual_entries'
    verbose_name = 'Manual Entries'
