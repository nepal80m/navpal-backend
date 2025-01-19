from django.shortcuts import render
from rest_framework.response import Response

# Create your views here.
from rest_framework import viewsets, mixins

from core.models import LocationHistory
from core.serializers import LocationHistorySerializer


class AudioViewSet(viewsets.ViewSet):
    def list(self, request):
        print("Hello")
        return Response({"audio": "audio list"})

    def create(self, request):
        # get file from request
        print(request.data)
        print(request.FILES)
        # read headers
        print(request.headers)

        return Response({"audio": "audio created"})


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
