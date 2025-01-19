from django.shortcuts import render
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
        # get file from request
        print(request.FILES)
        uploaded_file = request.FILES["file"]
        AudioFile.objects.create(file=uploaded_file)

        # print(uploaded_file)
        # audio_file = uploaded_file
        # transcription = client.audio.translations.create(
        #     model="whisper-1",
        #     file=audio_file,
        # )
        # print(transcription.text)

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
        # get file from request
        print(request.data)
        print(request.FILES)
        for filename, file in request.FILES.iteritems():
            name = request.FILES[filename].name
            print(name)
        return Response({"audio": "audio created"})
