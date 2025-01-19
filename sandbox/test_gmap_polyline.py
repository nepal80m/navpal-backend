# import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

import requests
from googlemaps import convert

with open("output/ex_directions.json", "r") as f:
    directions = json.load(f)

print("directions", end="===========================\n")

# print(directions[0])
encoded_polyline = directions[0]["legs"][0]["steps"][1]["polyline"]["points"]
decoded_points = convert.decode_polyline(encoded_polyline)
print(decoded_points)
with open("output/ex_polyline.json", "w") as f:
    json.dump(decoded_points, f)
