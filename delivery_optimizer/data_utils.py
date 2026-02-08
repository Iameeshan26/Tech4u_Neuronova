import numpy as np
import pandas as pd
import requests
import logging
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
    Fetches travel times and distances from TomTom Matrix API.
    Falls back to Haversine distance and constant speed if API fails or key is invalid.
    
    df_locations: DataFrame with 'lat', 'lon' columns.
    Returns: distances (matrix, meters), durations (matrix, seconds)
    """
    locations = []
    for _, row in df_locations.iterrows():
        locations.append({"point": {"latitude": row['lat'], "longitude": row['lon']}})
        
    url = f"https://api.tomtom.com/routing/matrix/2?key={config.TOMTOM_API_KEY}"
    
    payload = {
        "origins": locations,
        "destinations": locations,
        "options": {
            "travelMode": "truck",
            "traffic": "live",
            "departAt": "now"
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    use_fallback = True
    
    if config.TOMTOM_API_KEY != "YOUR_TOMTOM_API_KEY" and config.TOMTOM_API_KEY != "mock":
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"TomTom API Response: {data}")
                data_matrix = data['data']
                
                size = len(df_locations)
                dist_matrix = np.zeros((size, size))
                time_matrix = np.zeros((size, size))
                
                for i in range(size):
                    for j in range(size):
                        cell = data_matrix[i * size + j]
                        if 'routeSummary' in cell:
                            summary = cell['routeSummary']
                            dist_matrix[i][j] = summary['lengthInMeters']
                            time_matrix[i][j] = summary['travelTimeInSeconds']
                        else:
                            # Handle route failure within matrix (e.g. unreachable)
                             dist_matrix[i][j] = float('inf')
                             time_matrix[i][j] = float('inf')
                             
                logger.info("Successfully fetched TomTom Matrix data.")
                return dist_matrix, time_matrix
            else:
                logger.warning(f"TomTom API failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error calling TomTom API: {e}")
    else:
        logger.info("Using placeholder API key or explicit 'mock' mode. Skipping API call.")

    # Fallback Logic
    logger.info("Using Haversine fallback for matrix.")
    size = len(df_locations)
    dist_matrix = np.zeros((size, size))
    time_matrix = np.zeros((size, size))
    
    # speed in m/s (30 km/h = 8.33 m/s)
    speed_mps = config.FALLBACK_SPEED_KMH * 1000 / 3600 
    
    coords = df_locations[['lat', 'lon']].values
    
    for i in range(size):
        for j in range(size):
            if i == j:
                dist_matrix[i][j] = 0
                time_matrix[i][j] = 0
            else:
                dist = haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                dist_matrix[i][j] = dist
                time_matrix[i][j] = dist / speed_mps
                
    return dist_matrix, time_matrix
