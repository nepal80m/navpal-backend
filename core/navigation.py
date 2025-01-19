import math
import os
from scipy.spatial import KDTree
from googlemaps import convert
#################################
# If using the separate OpenAI client library:
from openai import OpenAI
#################################
# If using openai Python package, do: import openai

# ----------------------------------------------------------
# 1. OPENAI CLIENT & CONFIGURATION
# ----------------------------------------------------------

# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("OpenAI API key not set. Please set 'OPENAI_API_KEY' env variable.")

client = OpenAI()

def generate_text(prompt):
    """
    Call the LLM with a custom prompt, returning generated text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # or whichever model ID you have
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0,
            n=1,
            stop=None
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred with the LLM: {e}")
        return None

# ----------------------------------------------------------
# 2. HELPER FUNCTIONS
# ----------------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the Haversine distance between two points in meters.
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate the bearing between two points in degrees [0, 360).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = (math.cos(phi1) * math.sin(phi2)
         - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda))

    bearing = math.atan2(x, y)
    bearing_degrees = (math.degrees(bearing) + 360) % 360
    return bearing_degrees

def determine_direction_on_path(movement_bearing, path_bearing):
    """
    For 'On the path' scenario:
    - If the bearing difference is <= 90 or >= 270, consider it 'forward'.
    - Else, consider it 'backward'.
    This avoids contradictory left/right instructions when the user is actually on the path.
    """
    diff = (movement_bearing - path_bearing) % 360
    # We'll define forward vs backward by quadrant
    # e.g. if within 90° => forward, else => backward
    # (You can tune these angle bounds as needed)
    if diff <= 90 or diff >= 270:
        return 'forward'
    else:
        return 'backward'

def determine_direction_off_path(movement_bearing, path_bearing):
    """
    For 'Off the path' scenario, we allow left/right/backward/forward instructions
    to help the user rejoin the path.
    """
    diff = (movement_bearing - path_bearing) % 360

    if diff <= 45 or diff >= 315:
        return 'forward'
    elif 135 <= diff <= 225:
        return 'backward'
    elif 45 < diff < 135:
        return 'right'
    else:
        return 'left'

def provide_instructions(relative_direction):
    """
    Provide instructions based on the relative direction.
    """
    if relative_direction == 'forward':
        return 'Continue going forward.'
    elif relative_direction == 'backward':
        return 'You are moving away from the path. Please go back.'
    elif relative_direction == 'left':
        return 'You are deviating to the left. Please turn right to rejoin the path.'
    elif relative_direction == 'right':
        return 'You are deviating to the right. Please turn left to rejoin the path.'
    else:
        return 'Movement direction undetermined.'


# ----------------------------------------------------------
# 3. NAVIGATOR CLASS
# ----------------------------------------------------------

class Navigator:
    def __init__(self, directions):
        """
        Initialize the Navigator with directions from Google Maps API.
        
        Parameters:
            directions (list): Directions data from Google Maps.
        """
        self.directions = directions
        self.location_history = []   # Keep at most 2 points
        self.polyline_coords = []
        self.kd_tree = None
        self.threshold_meters = 15

        self.prepare_route()

    def prepare_route(self):
        """
        Decode all polylines and build a KDTree for nearest-path lookups.
        """
        all_coords = []
        for direction in self.directions:
            for leg in direction.get('legs', []):
                for step in leg.get('steps', []):
                    poly_str = step.get('polyline', {}).get('points', '')
                    if not poly_str:
                        continue
                    try:
                        decoded = convert.decode_polyline(poly_str)
                        coords = [(pt['lat'], pt['lng']) for pt in decoded]
                        all_coords.extend(coords)
                    except Exception as e:
                        print(f"Error decoding polyline: {e}")

        if all_coords:
            self.polyline_coords = all_coords
            self.kd_tree = KDTree(self.polyline_coords)
            print(f"KDTree built with {len(all_coords)} path points.")
        else:
            print("No valid path coordinates found. KDTree not built.")

    def get_navigation_instructions(self, current_lat, current_lng):
        """
        Returns (status, instruction) given the user's current (lat, lng).
        status -> "On the path" or "OFF the path"
        instruction -> A relevant instruction string
        """
        # Keep last 2 points only
        self.location_history.append((current_lat, current_lng))
        if len(self.location_history) > 2:
            self.location_history.pop(0)

        if not self.kd_tree:
            return "Error", "No route data (KDTree) available."

        # Find the nearest point on the path
        _, nearest_index = self.kd_tree.query((current_lat, current_lng))
        nearest_point = self.polyline_coords[nearest_index]

        # Calculate distance to path in meters
        distance_to_path = haversine_distance(
            current_lat, current_lng,
            nearest_point[0], nearest_point[1]
        )

        print(f"Current location: ({current_lat}, {current_lng})")
        print(f"Nearest path point: {nearest_point}")
        print(f"Distance to path: {distance_to_path:.2f} m")

        # Determine on/off path
        if distance_to_path <= self.threshold_meters:
            # On the path
            status = "On the path"
            instruction = "You are on the path."

            # If we have 2 points to compute bearings
            if len(self.location_history) == 2:
                prev_lat, prev_lng = self.location_history[0]
                movement_bearing = calculate_bearing(prev_lat, prev_lng, current_lat, current_lng)

                # Determine path bearing (approx) from nearest point to next
                if nearest_index < len(self.polyline_coords) - 1:
                    next_pt = self.polyline_coords[nearest_index + 1]
                    path_bearing = calculate_bearing(nearest_point[0], nearest_point[1],
                                                     next_pt[0], next_pt[1])
                elif nearest_index > 0:
                    prev_pt = self.polyline_coords[nearest_index - 1]
                    path_bearing = calculate_bearing(prev_pt[0], prev_pt[1],
                                                     nearest_point[0], nearest_point[1])
                else:
                    path_bearing = 0.0

                # Use the simplified direction logic for "on path"
                direction = determine_direction_on_path(movement_bearing, path_bearing)
                instruction = provide_instructions(direction)

        else:
            # OFF the path
            status = "OFF the path"
            if len(self.location_history) == 2:
                prev_lat, prev_lng = self.location_history[0]
                movement_bearing = calculate_bearing(prev_lat, prev_lng, current_lat, current_lng)
                bearing_to_path = calculate_bearing(current_lat, current_lng,
                                                    nearest_point[0], nearest_point[1])
                bearing_diff = (bearing_to_path - movement_bearing + 360) % 360
                if bearing_diff > 180:
                    bearing_diff -= 360
                turn_dir = "left" if bearing_diff > 0 else "right"
                instruction = (f"You have deviated from the path. "
                               f"Please go back and turn {turn_dir} to rejoin the path.")
            else:
                instruction = ("You are off the path at the start. "
                               "Not enough history for direction.")

        return status, instruction


# ----------------------------------------------------------
# 4. PROCESS SINGLE LOCATION UPDATE
# ----------------------------------------------------------

def process_location_update(navigator, loc, flight_status, time_until_flight, transcription):
    """
    Handle a single new location update. If OFF the path, 
    call the LLM with Nepali instructions.
    
    - navigator: Navigator instance
    - loc: {"lat": float, "lng": float}
    - flight_status: e.g. "On time", "Delayed", ...
    - time_until_flight: e.g. "2 hours", "45 minutes" ...
    - transcription: an object with .text indicating what the user asked
    """
    status, instruction = navigator.get_navigation_instructions(loc['lat'], loc['lng'])
    print(f"Location: {loc}")
    print(f"Status: {status}")

    if status == "OFF the path":
        # Build prompt in Nepali
        prompt = (
            f"Give output in Nepali language. A person is travelling on a path and give instruction to the person based on "
            f"the following information in nepali language. Person's status: {status}, Instruction: {instruction}. "
            f"Flight status: {flight_status}. Time until flight: {time_until_flight}. "
            f"Transcription of what person is asking: {transcription.text}. "
            f"Answer person's query based on their status, instruction and flight status and nothing else. "
            f"Be specific and don't tell anything more than what is asked."
        )
        result = generate_text(prompt)
        if result:
            print(f"LLM Instruction (Nepali): {result}\n")
        else:
            print("No LLM response.\n")

    elif status == "On the path":
        # Just print the local instruction; no LLM call needed
        print(f"Instruction: {result}\n")

    return result


# ----------------------------------------------------------
# 5. EXAMPLE USAGE
# ----------------------------------------------------------
if __name__ == "__main__":
    # Example directions data
    directions = [
        {
            "legs": [{
                "steps": [
                    {"polyline": {"points": "gdq`Hv|miVGO"}},
                    {"polyline": {"points": "odq`Hf|miVYj@U\\KXEHKJONIHIBGBi@FM?E?CAIAQIKUKBGICCKUOSIMQYEICEMe@MSACUSCEIMQYEIKQIMMSM]CEO["}}
                ]
            }]
        }
    ]

    # Initialize Navigator
    navigator = Navigator(directions)

    # Mock flight status and time
    flight_status = "On time"
    time_until_flight = "2 hours"

    # Simple transcription class
    class Transcription:
        def __init__(self, text):
            self.text = text

    # We'll store incoming locations but process them individually
    test_location_updates = []

    # 1) First update - on path
    loc1 = {"lat": 47.44276, "lng": -122.30108}
    test_location_updates.append(loc1)
    transcription_obj = Transcription("How far am I from the next step?")
    process_location_update(navigator, loc1, flight_status, time_until_flight, transcription_obj)

    # 2) Second update - also on path
    loc2 = {"lat": 47.4428, "lng": -122.301}
    test_location_updates.append(loc2)
    transcription_obj = Transcription("Am I still going the right way?")
    process_location_update(navigator, loc2, flight_status, time_until_flight, transcription_obj)

    # 3) Third update - user veers off path
    loc3 = {"lat": 47.443, "lng": -122.3009}
    test_location_updates.append(loc3)
    transcription_obj = Transcription("Which direction should I go now?")
    process_location_update(navigator, loc3, flight_status, time_until_flight, transcription_obj)