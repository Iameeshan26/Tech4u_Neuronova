"""
City-specific presets for the Neuronova Delivery Optimizer.
Allows the application to adapt to different urban environments.
"""

CITY_PROFILES = {
    "berlin": {
        "name": "Berlin, Germany",
        "avg_speed_kmh": 35.0,
        "weather_sensitivity": 1.2, # Moderate impact from rain/snow
        "urban_density": "medium",
        "default_center": (52.5200, 13.4050),
        "typical_fleet": [0, 1, 1] # Heavy truck + 2 Light Vans
    },
    "mumbai": {
        "name": "Mumbai, India",
        "avg_speed_kmh": 18.0, # High congestion
        "weather_sensitivity": 1.5, # High impact from Monsoon
        "urban_density": "extreme",
        "default_center": (19.0760, 72.8777),
        "typical_fleet": [2, 2, 1] # 2 Scooters + 1 Light Van
    },
    "nyc": {
        "name": "New York City, USA",
        "avg_speed_kmh": 22.0,
        "weather_sensitivity": 1.3,
        "urban_density": "high",
        "default_center": (40.7128, -74.0060),
        "typical_fleet": [1, 2, 2] # 1 Van + 4 Scooters
    },
    "default": {
        "name": "Generic City",
        "avg_speed_kmh": 30.0,
        "weather_sensitivity": 1.0,
        "urban_density": "medium",
        "default_center": (0.0, 0.0),
        "typical_fleet": [1, 1, 1]
    }
}

def get_city_profile(city_name):
    return CITY_PROFILES.get(city_name.lower(), CITY_PROFILES["default"])
