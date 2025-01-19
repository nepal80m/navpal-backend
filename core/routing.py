from django.urls import path
from .consumers import VoiceAssistantWebsocketConsumer
from django.urls import re_path

websocket_urlpatterns = [
    path("ws/voice-assistant/", VoiceAssistantWebsocketConsumer.as_asgi()),
]
