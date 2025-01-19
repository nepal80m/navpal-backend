from django.contrib import admin

# Register your models here.
from core.models import LocationHistory, AudioFile

admin.site.register(LocationHistory)
admin.site.register(AudioFile)
