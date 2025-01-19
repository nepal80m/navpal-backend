from django.urls import include, path
from .views import AudioViewSet, LocationHistoryViewSet, GPSViewSet
from rest_framework.routers import DefaultRouter, SimpleRouter

router = DefaultRouter()

router.register(r"audio", AudioViewSet, basename="audio")
router.register(
    r"location-history", LocationHistoryViewSet, basename="location-history"
)
app_name = "core"
urlpatterns = [] + router.urls
