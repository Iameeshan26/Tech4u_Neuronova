"""
Configuration settings for the Dynamic Last-Mile Delivery Optimizer.
"""

# API Keys
# Replace 'YOUR_TOMTOM_API_KEY' with your actual key in production or use environment variables
TOMTOM_API_KEY = "hmgjN6megL2dsacqy31Sjp5Oaa8FUgcv"

# Optimization Weights
# Cost = (time * w1) + (fuel * w2) + (PriorityPenalty * w3)
WEIGHT_TIME = 1.0
WEIGHT_FUEL = 0.5  # Assuming fuel roughly correlates with distance/time, but lower weight
WEIGHT_PRIORITY = 100.0 # High penalty for missing high priority or ordering issues

# Constraints
VEHICLE_CAPACITY = 40 # Max items per vehicle (Increased to cover ~25 demand of 10 stops)
NUM_VEHICLES = 1     # MVP assumes 1 vehicle for simplicity, scalable to N
DEPOT_INDEX = 0

# Dynamic Trigger Thresholds
# If predicted ETA deviates by more than this percentage, re-optimization might be triggered
REOPTIMIZATION_VARIANCE_THRESHOLD = 0.15 # 15%

# Other Constants
FALLBACK_SPEED_KMH = 30.0 # Average speed for Haversine time estimation
