import os
import time

from datetime import datetime, timezone

import csv


from apscheduler.schedulers.background import BackgroundScheduler


from django.core.files.storage import FileSystemStorage


from django.core.management.base import BaseCommand

from django.core.cache import cache

from core.models import AudioFile

from core import navigation


import requests
import googlemaps

from openai import OpenAI


GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")

gmaps = googlemaps.Client(key=GMAPS_API_KEY)


AS_KEY = os.getenv("AVIATIONSTACK_API_KEY")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()



# Simple transcription class

class Transcription:

    def __init__(self, text):

        self.text = text


def pull_flight_info(flight_number):
    params = {
      "access_key": AS_KEY,
      "flight_iata": flight_number,
    }

    api_result = requests.get("https://api.aviationstack.com/v1/flights", params)

    api_response = api_result.json()

    return api_response


def get_gate_coords(gate):
    from django.conf import settings
    csv_file=settings.BASE_DIR / "core/management/commands/gate_locs.csv"
    # csv_file = ("./gate_locs.csv")

    with open(csv_file, mode='r') as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row['GATE'].lower() == gate.lower():

                try:
                    latitude = float(row['LAT'])
                    longitude = float(row['LONG'])

                    return latitude, longitude

                except ValueError:

                    raise ValueError(f"Invalid data for gate {gate} in the CSV.")


    return None


def flight_data_to_dict(response):
    departure_data = response["data"][0]["departure"]
    flight_data = dict()

    flight_data["gate_str"] = departure_data["gate"]

    given_time_str = departure_data["estimated"]
    given_time = datetime.fromisoformat(given_time_str)
    current_time = datetime.now(timezone.utc)
    time_difference = given_time - current_time
    flight_data["time_until_flight"] = str(time_difference.seconds // 60) + " minutes"
    flight_data["flight_status"] = "On time" if not departure_data["estimated"] else "Delayed"

    return flight_data


def feedback_beat():
    with open("test.txt", "a") as f:
        f.write("asfasf\n")

    recent_coords = cache.get("recent_coords", default=[(47.4463438,-122.3042077)])

    user_input_text = cache.get("user_input_text", default=None)

    origin = ",".join([str(coord) for coord in recent_coords[0]])

    loc1 = {
        "lat": recent_coords[0][0],
        "lng": recent_coords[0][1],
    }

    if cache.get("flight_num", default=None) is None:
        # If starting navigation
        flight_no = "AS133"

        cache.set("flight_num", flight_no)

        response = pull_flight_info(flight_no)
        flight_data = flight_data_to_dict(response)
        
        destination = get_gate_coords(flight_data["gate_str"])
        dest_str = ",".join([str(coord) for coord in destination])

        directions = gmaps.directions(
            origin, dest_str, mode="walking", departure_time=datetime.now())

        # Initialize Navigator with the provided directions
        navigator = navigation.Navigator(directions)

        cache.set("destination", destination)
        cache.set("directions", directions)
        cache.set("flight_data", flight_data)

        transcription_obj = Transcription("")
        result = navigation.process_location_update(
            navigator, 
            loc1, 
            flight_data["flight_status"], 
            flight_data["time_until_flight"], 
            transcription_obj
        )

    elif user_input_text is not None:

        # If user input...

        user_input_lang = cache.get("user_input_lang", default=None)

        # Delete input from cache

        cache.delete("user_input_text")
        cache.delete("user_input_lang")
        
        directions = cache.get("directions")


        # Initialize Navigator with the provided directions

        navigator = navigation.Navigator(directions)


        # Do response to input

        transcription_obj = Transcription(user_input_text)
        result = navigation.process_location_update(
            navigator, 

            loc1, 

            flight_data["flight_status"], 

            flight_data["time_until_flight"], 

            transcription_obj
        )

        from django.conf import settings
        # base_path=settings.BASE_DIR

        speech_file_path = settings.BASE_DIR /"nova.mp3"
        response = client.audio.speech.create(

            model="tts-1",

            voice="nova",

            input=result,
        )
        response.stream_to_file(speech_file_path)

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        room_name = "room1"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"file_transfer_{room_name}",
            {"type": "send_audio_file", "file_path": speech_file_path},
        )


class Command(BaseCommand):

    help = 'Run navigation updates'


    def handle(self, *args, **kwargs):


        scheduler = BackgroundScheduler()


        scheduler.add_job(feedback_beat, 'interval', seconds=5)
        scheduler.start()

        self.stdout.write("Scheduler started. Press Ctrl+C to exit.")

        try:
            while True:
                time.sleep(1)


        except (KeyboardInterrupt, SystemExit):

            scheduler.shutdown()


