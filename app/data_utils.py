import numpy as np
import pandas as pd
import requests
import logging
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from math import radians, cos, sin, asin, sqrt
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_mock_data(num_stops=10):
    """
    Generates mock delivery locations in a city center (e.g., Berlin).
    Retuns a DataFrame with 'id', 'lat', 'lon', 'demand', 'priority'.
    """
    # Center coords (approx Berlin center)
    center_lat, center_lon = 52.5200, 13.4050
    
    # Generate random offsets
    np.random.seed(42) # For reproducibility
    lats = center_lat + np.random.uniform(-0.05, 0.05, num_stops)
    lons = center_lon + np.random.uniform(-0.05, 0.05, num_stops)
    
    data = []
    # Depot
    data.append({
        'id': 'Depot',
        'lat': center_lat,
        'lon': center_lon,
        'demand': 0,
        'priority': 0 # Depot has no priority
    })
    
    # Stops
    for i in range(num_stops):
        data.append({
            'id': f'Stop_{i+1}',
            'lat': lats[i],
            'lon': lons[i],
            'demand': np.random.randint(1, 5), # Random demand 1-4 items
            'priority': np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1]) # 1=Normal, 3=High
        })
        
    return pd.DataFrame(data)

def load_data_from_csv(filepath):
    """
    Loads delivery locations from a CSV file.
    Expected columns: id, lat, lon, demand, priority
    """
    try:
        df = pd.read_csv(filepath)
        required_columns = ['id', 'lat', 'lon', 'demand', 'priority']
        
        # Check if all required columns are present
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Missing required columns: {missing}")
            
        return df
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return None

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000 # Return meters

def get_tomtom_matrix(df_locations):
    """
    Fetches travel times and distances for a DataFrame of locations.
    """
    # 1. Try Loading from Cache
    cache_data = _load_matrix_cache(df_locations)
    if cache_data:
        logger.info("Using cached distance/time matrix.")
        return cache_data

    locations = []
    for _, row in df_locations.iterrows():
        locations.append((row['lat'], row['lon']))
    
    dist_matrix, time_matrix = get_tomtom_matrix_from_points(locations)
    
    # Save to Cache
    _save_matrix_cache(df_locations, dist_matrix, time_matrix)
    
    return dist_matrix, time_matrix

def get_tomtom_matrix_from_points(points):
    """
    Fetches travel times and distances for a list of (lat, lon) tuples.
    No automatic caching here (caching handled at higher level).
    """
    size = len(points)
    dist_matrix = np.zeros((size, size))
    time_matrix = np.zeros((size, size))
    
    if config.TOMTOM_API_KEY == "YOUR_TOMTOM_API_KEY" or config.TOMTOM_API_KEY == "mock":
        logger.info("Using placeholder API key or explicit 'mock' mode. Skipping API call.")
        return _haversine_fallback_from_points(points)

    locations = [{"point": {"latitude": lat, "longitude": lon}} for lat, lon in points]
    url = f"https://api.tomtom.com/routing/matrix/2?key={config.TOMTOM_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    try:
        logger.info(f"Fetching TomTom Matrix in parallel ({size} origins)...")
        
        def fetch_row(i):
            payload = {
                "origins": [locations[i]],
                "destinations": locations,
                "options": {"travelMode": "truck", "traffic": "live", "departAt": "now"}
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return i, data['data']
            else:
                logger.warning(f"TomTom API failed for origin {i} with status {response.status_code}")
                return i, None

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(fetch_row, range(size)))

        for i, row_data in results:
            if row_data:
                for j in range(size):
                    cell = row_data[j]
                    if 'routeSummary' in cell:
                        summary = cell['routeSummary']
                        dist_matrix[i][j] = summary['lengthInMeters']
                        time_matrix[i][j] = summary['travelTimeInSeconds']
                    else:
                        dist_matrix[i][j] = float('inf')
                        time_matrix[i][j] = float('inf')
            else:
                _fill_haversine_row_from_points(points, dist_matrix, time_matrix, i)
        
        return dist_matrix, time_matrix

    except Exception as e:
        logger.error(f"Error calling TomTom API matrix: {e}")
        return _haversine_fallback_from_points(points)

def _haversine_fallback_from_points(points):
    size = len(points)
    dist_matrix = np.zeros((size, size))
    time_matrix = np.zeros((size, size))
    for i in range(size):
        _fill_haversine_row_from_points(points, dist_matrix, time_matrix, i)
    return dist_matrix, time_matrix

def _fill_haversine_row_from_points(points, dist_matrix, time_matrix, i):
    size = len(points)
    speed_mps = config.FALLBACK_SPEED_KMH * 1000 / 3600 
    for j in range(size):
        if i == j:
            dist_matrix[i][j] = 0
            time_matrix[i][j] = 0
        else:
            dist = haversine_distance(points[i][0], points[i][1], points[j][0], points[j][1])
            dist_matrix[i][j] = dist
            time_matrix[i][j] = dist / speed_mps

def _load_matrix_cache(df):
    # Cache is in root/data/
    root_dir = os.path.dirname(os.path.dirname(__file__))
    cache_path = os.path.join(root_dir, "data", config.CACHE_FILE)
    if not os.path.exists(cache_path):
        return None
        
    try:
        with open(cache_path, 'r') as f:
            cache = json.load(f)
            
        # Validate TTL
        if time.time() - cache['timestamp'] > config.CACHE_TTL:
            logger.info("Cache expired.")
            return None
            
        # Validate Hash (Simplified: check location count and first/last coords)
        if cache['size'] != len(df):
            return None
            
        return np.array(cache['dist']), np.array(cache['time'])
    except Exception as e:
        logger.warning(f"Error loading cache: {e}")
        return None

def _save_matrix_cache(df, dist, time_mat):
    root_dir = os.path.dirname(os.path.dirname(__file__))
    cache_path = os.path.join(root_dir, "data", config.CACHE_FILE)
    cache = {
        "timestamp": time.time(),
        "size": len(df),
        "dist": dist.tolist(),
        "time": time_mat.tolist()
    }
    with open(cache_path, 'w') as f:
        json.dump(cache, f)

def _fill_haversine_row(df_locations, dist_matrix, time_matrix, i):
    size = len(df_locations)
    speed_mps = config.FALLBACK_SPEED_KMH * 1000 / 3600 
    coords = df_locations[['lat', 'lon']].values
    for j in range(size):
        if i == j:
            dist_matrix[i][j] = 0
            time_matrix[i][j] = 0
        else:
            dist = haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            dist_matrix[i][j] = dist
            time_matrix[i][j] = dist / speed_mps

def _haversine_fallback(df_locations):
    logger.info("Using Haversine fallback for matrix.")
    size = len(df_locations)
    dist_matrix = np.zeros((size, size))
    time_matrix = np.zeros((size, size))
    for i in range(size):
        _fill_haversine_row(df_locations, dist_matrix, time_matrix, i)
    return dist_matrix, time_matrix

def get_tomtom_route(locations_sequence):
    """
    Fetches the detailed routing path between a sequence of locations using TomTom Routing API.
    locations_sequence: List of (lat, lon) tuples.
    Returns: List of (lat, lon) tuples representing the detailed path.
    """
    if len(locations_sequence) < 2:
        return locations_sequence

    # TomTom Calculate Route expects waypoints in the URL as:
    # origin:destination:waypoint1:waypoint2...
    # But for simplicity and to handle many waypoints, we can use the POST method if needed.
    # For now, let's use the GET method as it's common for simple sequences.
    
    # Format: lat,lon:lat,lon:...
    points_str = ":".join([f"{lat},{lon}" for lat, lon in locations_sequence])
    
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{points_str}/json?key={config.TOMTOM_API_KEY}"
    
    params = {
        "routeType": "fastest",
        "travelMode": "truck"
    }

    if config.TOMTOM_API_KEY != "YOUR_TOMTOM_API_KEY" and config.TOMTOM_API_KEY != "mock":
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully fetched TomTom Routing data.")
                
                # Extract coordinates from the response
                # data['routes'][0]['legs'] contains points for each leg
                detailed_path = []
                for route in data.get('routes', []):
                    for leg in route.get('legs', []):
                        for point in leg.get('points', []):
                            detailed_path.append((point['latitude'], point['longitude']))
                
                if detailed_path:
                    return detailed_path
            else:
                logger.warning(f"TomTom Routing API failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error calling TomTom Routing API: {e}")

    # Fallback: return the original sequence (straight lines)
    logger.info("Using straight-line fallback for route visualization.")
    return locations_sequence


def get_current_weather(lat, lon):
    """
    Fetches current weather for a specific location using OpenWeatherMap API.
    Returns: Condition (e.g., 'Rain', 'Clear') or None if failed.
    """
    if not config.OPEN_WEATHER_API_KEY:
        logger.warning("OpenWeatherMap API key not found in configuration.")
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": config.OPEN_WEATHER_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            condition = data['weather'][0]['main']
            logger.info(f"Current weather at ({lat}, {lon}): {condition}")
            return condition
        else:
            logger.warning(f"OpenWeatherMap API failed with status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error calling OpenWeatherMap API: {e}")

    return None


def apply_weather_impact(time_matrix, weather_condition):
    """
    Adjusts the travel time matrix based on weather conditions.
    """
    impact_factor = config.WEATHER_IMPACT_FACTORS.get(weather_condition, config.DEFAULT_WEATHER_IMPACT)
    
    if impact_factor == 1.0:
        return time_matrix

    logger.info(f"Applying weather impact factor of {impact_factor} for {weather_condition}")
    return time_matrix * impact_factor
