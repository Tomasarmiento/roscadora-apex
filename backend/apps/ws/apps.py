from django.apps import AppConfig
from .utils.functions import init_channel_info


class WsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ws'

    def ready(self):
        from .models import ChannelInfo
        init_channel_info(ChannelInfo)
        # pass
