from apps.parameters.utils.functions import init_params
from django.apps import AppConfig


class ParametersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.parameters'

    def ready(self):
        init_params()
        # pass
