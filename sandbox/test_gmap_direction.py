# import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

import requests
import googlemaps

load_dotenv()

GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")

gmaps = googlemaps.Client(key=GMAPS_API_KEY)

# origin = "47.4489,-122.3094"  # Example starting point in SeaTac
# destination = "47.4505,-122.3100"  # Example restroom coordinates from Step 1
# origin = "Gate C43, Denver, CO 80249"
# destination = "Gate C47, Denver, CO 80249"
origin = "47.442172408455654,-122.30176724814764" # SEATAC A1
# destination = "47.44171253994404,-122.30345167540902" # SEATAC B8
destination = "47.445799588921886,-122.3005783994873" # SEATAC D4

response = gmaps.directions(
    origin, destination, mode="walking", departure_time=datetime.now())

# # url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&mode=walking&key={MAPS_SECRET_KEY}"
# https://www.google.com/maps/dir/39.8631648,-104.6723894/39.8631549,-104.6717039/@39.8673277,-104.6775821,15.95z?entry=ttu&g_ep=EgoyMDI1MDExNS4wIKXMDSoASAFQAw%3D%3D
# 39.8631648,-104.6723894/39.8631549,-104.6717039/@39.8673277,-104.6775821,15.95z?entry=ttu&g_ep=EgoyMDI1MDExNS4wIKXMDSoASAFQAw%3D%3D

# Print step-by-step directions
with open("output/ex_directions.json", "w") as f:
    json.dump(response, f)
