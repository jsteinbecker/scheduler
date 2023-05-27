from django.apps import AppConfig


class EmplConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empl'

    def ready(self):
        import empl.signals