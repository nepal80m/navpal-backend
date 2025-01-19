import math
from scipy.spatial import KDTree

# ----------------------------------
# Module-level history of locations
# ----------------------------------
LOCATION_HISTORY = []  # Will store (lat, lng) tuples

# ----------------------------------
# HELPER FUNCTIONS
# ----------------------------------
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
    
    distance = R * c
    return distance

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

def determine_direction(movement_bearing, path_bearing):
    """
    Determine the relative direction of movement compared to the path.
    Returns one of: 'forward', 'backward', 'left', 'right'.
    """
    # Calculate the bearing difference (0° means same direction)
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
    Provide instructions based on the relative direction on the path.
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

# ----------------------------------
# MAIN FUNCTION
# ----------------------------------
def get_navigation_instructions(current_lat, current_lng, polyline_steps):
    """
    Given the current location (lat, lng) and a new polyline (list of dicts 
    with keys 'lat' and 'lng'), return (status, instruction).

    status  -> "On the path" or "OFF the path"
    instruction -> Current navigation instruction based on the latest position.
    
    The function keeps track of historical locations so it can determine 
    movement bearing from the previous location to the current location.
    """
    # 1) Append current location to our LOCATION_HISTORY
    LOCATION_HISTORY.append((current_lat, current_lng))
    
    # 2) Build a KDTree from the updated polyline
    polyline_coords = [(step['lat'], step['lng']) for step in polyline_steps]
    tree = KDTree(polyline_coords)
    
    # 3) Find nearest path point
    threshold_meters = 15  # Distance threshold to consider "on path"
    # The tree.query(...) gives distance in terms of coordinate space (degrees),
    # so we must then use haversine_distance for accurate meters:
    nearest_index = tree.query((current_lat, current_lng))[1]
    nearest_point = polyline_coords[nearest_index]

    distance_to_nearest = haversine_distance(current_lat, current_lng,
                                             nearest_point[0], nearest_point[1])

    # 4) Determine if we can compute movement bearing 
    #    (this requires at least one previous point).
    movement_bearing = None
    if len(LOCATION_HISTORY) > 1:
        prev_lat, prev_lng = LOCATION_HISTORY[-2]  # second-last entry
        movement_bearing = calculate_bearing(prev_lat, prev_lng, 
                                             current_lat, current_lng)
    
    # 5) On-path vs. Off-path logic
    if distance_to_nearest <= threshold_meters:
        status = "On the path"
        if movement_bearing is not None:
            # Determine the path segment bearing
            if nearest_index < len(polyline_steps) - 1:
                # Bearing forward to next point
                path_bearing = calculate_bearing(
                    polyline_steps[nearest_index]['lat'], 
                    polyline_steps[nearest_index]['lng'],
                    polyline_steps[nearest_index + 1]['lat'], 
                    polyline_steps[nearest_index + 1]['lng']
                )
            elif nearest_index > 0:
                # Bearing backward from previous to current
                path_bearing = calculate_bearing(
                    polyline_steps[nearest_index - 1]['lat'], 
                    polyline_steps[nearest_index - 1]['lng'],
                    polyline_steps[nearest_index]['lat'], 
                    polyline_steps[nearest_index]['lng']
                )
            else:
                # If there's only one point in polyline, or we are at start
                path_bearing = 0.0

            # Compare movement bearing with path bearing
            relative_direction = determine_direction(movement_bearing, path_bearing)
            instruction = provide_instructions(relative_direction)
        else:
            # No movement yet (e.g. first location)
            instruction = "Standing on the path. No movement to analyze."
    else:
        status = "OFF the path"
        if movement_bearing is not None:
            # Bearing from current location to nearest path point
            bearing_to_path = calculate_bearing(current_lat, current_lng,
                                                nearest_point[0], nearest_point[1])
            # Compare with movement bearing
            bearing_diff = (bearing_to_path - movement_bearing + 360) % 360
            # Normalize to [-180, 180] for left/right logic
            if bearing_diff > 180:
                bearing_diff -= 360

            if bearing_diff > 0:
                turn_direction = 'left'
            else:
                turn_direction = 'right'

            instruction = (f"You have deviated from the path. "
                           f"Please go back and turn {turn_direction} to rejoin the path.")
        else:
            # If no previous location is known
            instruction = ("You are off the path at the start. "
                           "Please move closer to the path.")
    
    # 6) Return the *current* status and instruction
    return status, instruction

# ----------------------
# EXAMPLE USAGE (TEST)
# ----------------------
if __name__ == "__main__":
    # Define an example polyline
    example_polyline = [
        {"lat": 47.4428, "lng": -122.3010},
    {"lat": 47.44293, "lng": -122.30122},
    {"lat": 47.44304, "lng": -122.30137},
    {"lat": 47.44310, "lng": -122.30150},
    {"lat": 47.44313, "lng": -122.30155},
    {"lat": 47.44319, "lng": -122.30161},
    {"lat": 47.44327, "lng": -122.30169},
    {"lat": 47.44332, "lng": -122.30174},
    {"lat": 47.44337, "lng": -122.30176},
    {"lat": 47.44341, "lng": -122.30178},
    {"lat": 47.44362, "lng": -122.30182},
    {"lat": 47.44369, "lng": -122.30182},
    {"lat": 47.44372, "lng": -122.30182},
    {"lat": 47.44374, "lng": -122.30181},
    {"lat": 47.44379, "lng": -122.30180},
    {"lat": 47.44388, "lng": -122.30175},
    {"lat": 47.44394, "lng": -122.30164},
    {"lat": 47.44400, "lng": -122.30166},
    {"lat": 47.44404, "lng": -122.30161},
    {"lat": 47.44406, "lng": -122.30159},
    {"lat": 47.44412, "lng": -122.30148},
    {"lat": 47.44420, "lng": -122.30138},
    {"lat": 47.44425, "lng": -122.30131},
    {"lat": 47.44434, "lng": -122.30118},
    {"lat": 47.44437, "lng": -122.30113},
    {"lat": 47.44439, "lng": -122.30110},
    {"lat": 47.44446, "lng": -122.30091},
    {"lat": 47.44453, "lng": -122.30081},
    {"lat": 47.44454, "lng": -122.30079},
    {"lat": 47.44465, "lng": -122.30069},
    {"lat": 47.44467, "lng": -122.30066},
    {"lat": 47.44472, "lng": -122.30059},
    {"lat": 47.44481, "lng": -122.30046},
    {"lat": 47.44484, "lng": -122.30041},
    {"lat": 47.44490, "lng": -122.30032},
    {"lat": 47.44495, "lng": -122.30025},
    {"lat": 47.44502, "lng": -122.30015},
    {"lat": 47.44509, "lng": -122.30000},
    {"lat": 47.44511, "lng": -122.29997},
    {"lat": 47.44519, "lng": -122.29983},
    ]
    
    # # Simulate calls for a series of updates:
    # location_updates = [
    #     (47.44320, -122.30160),  # on path
    #     (47.44335, -122.30180),  # off path to the right
    #     (47.44330, -122.30175),  # returning
    # ]
    location_updates = [
    # On-path movements
    {"lat": 47.44320, "lng": -122.30160},
    {"lat": 47.44325, "lng": -122.30165},
    {"lat": 47.44327, "lng": -122.30169},
    {"lat": 47.44330, "lng": -122.30175},
    
    # Off-path movement: deviating to the right
    {"lat": 47.44335, "lng": -122.30180},
    
    # Off-path movement: deviating to the left
    {"lat": 47.44340, "lng": -122.30170},
    
    # Returning to path
    {"lat": 47.44335, "lng": -122.30175},
    {"lat": 47.44330, "lng": -122.30170},
    {"lat": 47.44325, "lng": -122.30165},
    {"lat": 47.44320, "lng": -122.30160},
    {"lat": 47.44509, "lng": -122.30000},
    {"lat": 47.44511, "lng": -122.29997},
    {"lat": 47.44519, "lng": -122.29983}
    ]

    status, instruction = get_navigation_instructions(47.44335, -122.30175, example_polyline)

    print(f"Status: {status}")
    print(f"Instruction: {instruction}")

    # for i, lat in enumerate(location_updates, start=1):
    #     print(lat['lat'], lat['lng'])
    #     status, instruction = get_navigation_instructions(lat['lat'], lat['lng'], example_polyline)
    #     print(f"Update {i} => Status: {status}, Instruction: {instruction}")