import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

# Optimization Weights
# Cost = (time * w1) + (fuel * w2) + (PriorityPenalty * w3)
WEIGHT_TIME = 1.0
WEIGHT_FUEL = 0.5  # Assuming fuel roughly correlates with distance/time, but lower weight
WEIGHT_PRIORITY = 100.0 # High penalty for missing high priority or ordering issues

# Constraints
VEHICLE_CAPACITY = 30 # Default max items per vehicle
NUM_VEHICLES = 3     # Total vehicles in fleet
DEPOT_INDEX = 0

# Vehicle Profiles (Heterogeneous Fleet)
VEHICLE_PROFILES = [
    {
        "id": 0,
        "name": "Heavy Truck",
        "capacity": 40,
        "cost_multiplier": 1.5, # More expensive to run
        "speed_factor": 0.8     # Slower
    },
    {
        "id": 1,
        "name": "Light Van",
        "capacity": 20,
        "cost_multiplier": 1.0, # Standard cost
        "speed_factor": 1.2     # Faster
    },
    {
        "id": 2,
        "name": "Electric Scooter",
        "capacity": 10,
        "cost_multiplier": 0.5, # Very cheap
        "speed_factor": 1.1     # Nimble in traffic
    }
]

# Cache Settings
CACHE_FILE = "matrix_cache.json"
CACHE_TTL = 3600 # 1 hour

# Dynamic Trigger Thresholds
# If predicted ETA deviates by more than this percentage, re-optimization might be triggered
REOPTIMIZATION_VARIANCE_THRESHOLD = 0.15 # 15%

# City-Agnostic Configuration
from city_configs import get_city_profile

# Active City Profile (Can be overridden at runtime)
ACTIVE_CITY = os.getenv("NEURONOVA_CITY", "berlin")
CITY_PROFILE = get_city_profile(ACTIVE_CITY)

# Fallback Constants (Informed by city profile)
FALLBACK_SPEED_KMH = CITY_PROFILE["avg_speed_kmh"]

# Weather Impact Factors (Multipliers for travel time)
_base_weather_impact = {
    "Clear": 1.0,
    "Clouds": 1.05,
    "Rain": 1.25,
    "Drizzle": 1.15,
    "Thunderstorm": 1.4,
    "Snow": 1.6,
    "Mist": 1.1,
    "Fog": 1.2,
}

# Scale weather impact based on city sensitivity
WEATHER_IMPACT_FACTORS = {
    k: 1.0 + (v - 1.0) * CITY_PROFILE["weather_sensitivity"]
    for k, v in _base_weather_impact.items()
}
DEFAULT_WEATHER_IMPACT = 1.0

# Routing API Configuration
ROUTING_API_URL = "https://api.tomtom.com/routing/matrix/2"
ROUTING_API_KEY = TOMTOM_API_KEY
