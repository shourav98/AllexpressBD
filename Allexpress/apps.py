from django.apps import AppConfig

class AllexpressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Allexpress'

    def ready(self):
        # Import components to register them
        from . import components
        