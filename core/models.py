from django.db import models

# Create your models here.


class LocationHistory(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)


class AudioFile(models.Model):
    file = models.FileField(upload_to="audio/")
    timestamp = models.DateTimeField(auto_now_add=True)
    translation = models.TextField()
