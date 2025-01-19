from core.models import LocationHistory

from rest_framework import serializers


class LocationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationHistory
        fields = "__all__"
