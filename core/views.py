import os
import io

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache
from django.conf import settings
from rest_framework.response import Response

# Create your views here.
from rest_framework import viewsets, mixins

from core.models import LocationHistory
from core.serializers import LocationHistorySerializer
from core.models import AudioFile
from openai import OpenAI

client = OpenAI()

class AudioViewSet(viewsets.ViewSet):
    def list(self, request):
        print("Hello")
        return Response({"audio": "audio list"})

    def create(self, request):
        """
        Speech audio file posted
        """
        # get file from request
        print(request.FILES)
        uploaded_file = request.FILES["file"]
        AudioFile.objects.create(file=uploaded_file)

        temp_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        file_path = temp_storage.save(f"temp/{uploaded_file.name}", uploaded_file)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        with open(full_path, "rb") as f:
            response = client.audio.translations.create(
                model="whisper-1",
                file=f,
            )

        print(response.text)

        # Save user input in cache
        cache.set("user_input_text", response.text, timeout=30)
        cache.set("user_input_lang", response.language, timeout=30)

        # Clean up: Remove the temporary file
        temp_storage.delete(file_path)

        # print(request.data)
        # print(request.FILES)
        # # read headers
        # print(request.headers)

        return Response({"message": "Audio Received."})


class LocationHistoryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = LocationHistory.objects.all()
    serializer_class = LocationHistorySerializer


class GPSViewSet(viewsets.ViewSet):
    def list(self, request):
        print("Hello")
        return Response({"audio": "audio list"})

    def create(self, request):
        """
        Updated user location posted, added
        """
        # get file from request
        print(request.data)
        print(request.FILES)

        recent_entries = LocationHistory.objects.order_by('-timestamp')[:2]
        recent_coords = [
            {
                "lat": entry.latitude,
                "lng": entry.longitude,
            }
            for entry in recent_entries
        ]
        cache.set("recent_coords", recent_coords, timeout=10)

        for filename, file in request.FILES.iteritems():
            name = request.FILES[filename].name
            print(name)
        return Response({"audio": "audio created"})
