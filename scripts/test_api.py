import requests
import time
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

BASE_URL = "http://localhost:8000"

# Sample locations from the existing locations.csv logic
locations = [
    {"id": "Depot", "lat": 52.5200, "lon": 13.4050, "demand": 0, "priority": 0},
    {"id": "Stop_1", "lat": 52.5300, "lon": 13.4150, "demand": 2, "priority": 1},
    {"id": "Stop_2", "lat": 52.5100, "lon": 13.3950, "demand": 3, "priority": 2},
]

def test_optimization():
    print("Testing Root...")
    print(requests.get(f"{BASE_URL}/").json())

    print("\nRequesting Optimization...")
    payload = {"locations": locations}
    response = requests.post(f"{BASE_URL}/optimize", json=payload)
    
    if response.status_code == 200:
        job_id = response.json()['job_id']
        print(f"Job IDs created: {job_id}")
        
        # Polling
        for _ in range(10):
            time.sleep(2)
            status_resp = requests.get(f"{BASE_URL}/status/{job_id}").json()
            print(f"Status: {status_resp['status']}")
            if status_resp['status'] == 'completed':
                print("Success! Route calculated.")
                print(f"Total Distance: {status_resp['result']['total_distance']}m")
                break
    else:
        print(f"Failed to start optimization: {response.text}")

if __name__ == "__main__":
    test_optimization()
