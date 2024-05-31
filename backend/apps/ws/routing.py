from django.urls import re_path

from . import consumers


websocket_urlpatterns = [
    # re_path(r'ws/graphs/', consumers.GraphsConsumer.as_asgi()),     # ws://localhost:8000/ws/graphs/
    re_path(r'ws/front/', consumers.FrontConsumer.as_asgi()),               # ws://localhost:8000/ws/front/
    re_path(r'ws/micro/data/', consumers.MicroDataConsumer.as_asgi()),      # ws://localhost:8000/ws/micro/
    re_path(r'ws/micro/log/', consumers.MicroLogConsumer.as_asgi()),        # ws://localhost:8000/ws/micro/
]