from django.urls import include, path
from .views import AudioViewSet
from rest_framework.routers import DefaultRouter, SimpleRouter

router = DefaultRouter()

router.register(r"audio", AudioViewSet, basename="audio")

urlpatterns = [] + router.urls
