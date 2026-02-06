# Walkthrough - Dynamic Last-Mile Delivery Optimizer MVP

I have successfully built the Python-based MVP for the Dynamic Last-Mile Delivery Optimizer. The system uses **Google OR-Tools** for routing, **TomTom Matrix API** (with robust fallback), and **Folium** for visualization.

## Key Features Implemented

### 1. Modular Architecture
The code is organized into clear modules:
- [config.py](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/config.py): Centralized configuration for API keys, weights, and thresholds.
- [data_utils.py](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/data_utils.py): Handles mock data generation and the dual-strategy matrix fetching (API -> Fallback).
- [optimizer.py](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/optimizer.py): Encapsulates the OR-Tools VRP logic with time windows, capacity, and multi-objective costs.
- [main.py](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/main.py): Orchestrates the entire flow and simulates dynamic events.

### 2. Robust Matrix Integration
- **Primary**: Tries to fetch live traffic data from TomTom Matrix API.
- **Fallback**: Automatically defaults to Haversine distance calculations (30km/h avg speed) if the API fails or the key is invalid.
- *Verified*: During testing, the system correctly identified an API issue and switched to the Haversine fallback without crashing.

### 3. Smart Optimization
- **Constraints**: 
    - Vehicle Capacity (Demand vs Capacity).
    - Time Windows (Simulated Morning/Afternoon slots).
- **Objectives**: 
    - Minimizes a weighted cost of Time, Fuel (Distance), and Priority Penalties.
    - Successfully drops nodes (with penalty) if constraints make them unreachable.

### 4. Dynamic Trigger Logic
- Implemented [check_reoptimization(current_eta, predicted_eta)](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/main.py#13-22) which flags for re-optimization if ETA variance exceeds 15%.
- *Verified*: Simulation scenarios showed:
    - 10% delay -> No action.
    - 20% delay -> **RE-OPTIMIZE TRIGGERED**.

## How to Run

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Optimizer**:
    ```bash
    python3 main.py
    ```

3.  **View Results**:
    - The script prints the optimal route sequence and dropped nodes to the console.
    - A map is generated: `route_map.html`. Open this in any browser to see the visualized route.

## Simulation Output Example

```text
Running Optimizer...
Objective: 40011966
Dropped nodes: [1, 2, 3, 6]
Route for vehicle 0:
 0 Time(1190,12593) -> 7 Time(...) -> ... -> 0 Time(...)
Distance of the route: 19304m
Time of the route: 2316s
...
>> RE-OPTIMIZE TRIGGERED!
```

## Next Steps
- **Production API Key**: Update [config.py](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/config.py) with a fully valid TomTom API key.
- **Real Data**: Replace [generate_mock_data](file:///Users/deeshan/Documents/Neuronova/delivery_optimizer/data_utils.py#12-46) with a CSV loader or database connection.
- **Frontend**: Build a web dashboards to display the `route_map.html` dynamically.
