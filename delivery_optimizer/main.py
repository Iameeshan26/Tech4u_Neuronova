import pandas as pd
import folium
import logging
import os
import config
import data_utils
from optimizer import RouteOptimizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_reoptimization(current_eta, predicted_eta):
    """
    Checks if re-optimization is needed based on ETA variance.
    Returns True if variance > threshold.
    """
    if predicted_eta == 0: return False
    variance = abs(current_eta - predicted_eta) / predicted_eta
    logger.info(f"ETA Variance: {variance:.2%}")
    return variance > config.REOPTIMIZATION_VARIANCE_THRESHOLD

def visualize_route(df_data, routes, filename="route_map.html"):
    """
    Creates a Folium map visualizing the routes.
    """
    if not routes:
        logger.warning("No routes to visualize.")
        return

    # Center map on Depot
    depot = df_data.iloc[config.DEPOT_INDEX]
    m = folium.Map(location=[depot['lat'], depot['lon']], zoom_start=13)

    colors = ['blue', 'green', 'red', 'purple', 'orange']
    
    # Plot points
    for i, row in df_data.iterrows():
        color = 'black' if i == config.DEPOT_INDEX else 'red'
        icon = 'home' if i == config.DEPOT_INDEX else 'info-sign'
        
        popup_text = f"{row['id']} (Pri: {row['priority']})"
        folium.Marker(
            [row['lat'], row['lon']],
            popup=popup_text,
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(m)

    # Plot routes
    for route in routes:
        vehicle_id = route['vehicle']
        sequence_indices = route['sequence']
        
        route_coords = []
        for idx in sequence_indices:
            row = df_data.iloc[idx]
            route_coords.append((row['lat'], row['lon']))
            
        folium.PolyLine(
            route_coords,
            color=colors[vehicle_id % len(colors)],
            weight=2.5,
            opacity=1
        ).add_to(m)
        
    m.save(filename)
    logger.info(f"Map saved to {filename}")

import argparse
import sys

def main():
    logger.info("Starting Dynamic Last-Mile Delivery Optimizer MVP...")
    
    # 1. Load Data (Hardcoded to locations.csv)
    file_path = os.path.join(os.path.dirname(__file__), 'locations.csv')
    logger.info(f"Loading data from {file_path}...")
    df = data_utils.load_data_from_csv(file_path)

    if df is None:
        logger.error("Failed to load data from CSV. Exiting.")
        return
    
    print("Delivery Locations:")
    print(df[['id', 'demand', 'priority']])
    
    # 2. Get Distance/Time Matrix (API or Fallback)
    logger.info("Fetching distance/time matrix...")
    dist_matrix, time_matrix = data_utils.get_tomtom_matrix(df)
    
    # 3. Optimize
    logger.info("Running Optimizer...")
    optimizer = RouteOptimizer(df, dist_matrix, time_matrix)
    solution = optimizer.solve()
    
    if solution:
        routes = optimizer.print_solution()
        
        # 4. Visualization
        visualize_route(df, routes)
        
        # 5. Dynamic Trigger Simulation
        # Simulate a delay or traffic change to test the trigger
        logger.info("\n--- Simulating Dynamic Trigger ---")
        
        # Assume initial estimated time for Route 0 is T_est
        if routes:
            initial_eta = routes[0]['time']
            
            # Scenario A: Minor delay (10%)
            logger.info("Scenario A: Minor delay (10%)")
            new_eta_minor = initial_eta * 1.10
            if check_reoptimization(new_eta_minor, initial_eta):
                logger.info(">> RE-OPTIMIZE TRIGGERED!")
            else:
                logger.info(">> Variance within limits. No action.")
                
            # Scenario B: Major delay (20%)
            logger.info("Scenario B: Major delay (20%)")
            new_eta_major = initial_eta * 1.20
            if check_reoptimization(new_eta_major, initial_eta):
                logger.info(">> RE-OPTIMIZE TRIGGERED!")
            else:
                logger.info(">> Variance within limits. No action.")
                
    else:
        logger.error("Failed to find a solution.")

if __name__ == "__main__":
    main()
