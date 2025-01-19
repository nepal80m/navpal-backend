import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

AS_KEY = os.getenv("AVIATIONSTACK_API_KEY")

params = {
  "access_key": AS_KEY,
}

with open("output/ex_flights.json", "w") as f:
    api_result = requests.get("https://api.aviationstack.com/v1/flights", params)

    api_response = api_result.json()

    json.dump(api_response, f)

