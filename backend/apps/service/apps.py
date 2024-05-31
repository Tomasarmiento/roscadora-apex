from django.apps import AppConfig
from .api.service import start_service


class ServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.service'

    def ready(self):
        start_service()
        print("start service")
        # pass
