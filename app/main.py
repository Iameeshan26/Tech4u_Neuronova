import pandas as pd
import folium
import logging
import os
import config
import data_utils
import time
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
    
        # 1. Get simple sequence of stops
        stop_coords = []
        for idx in sequence_indices:
            row = df_data.iloc[idx]
            stop_coords.append((row['lat'], row['lon']))
            
        # 2. Get detailed routing path from TomTom
        logger.info(f"Fetching detailed route for vehicle {vehicle_id}...")
        route_coords = data_utils.get_tomtom_route(stop_coords)
            
        folium.PolyLine(
            route_coords,
            color=colors[vehicle_id % len(colors)],
            weight=2.5,
            opacity=1
        ).add_to(m)

        
    m.save(filename)
    logger.info(f"Map saved to {filename}")

def generate_logistics_dashboard(routes, weather, output_path):
    """
    Generates a premium HTML report with logistics metrics and ETAs.
    """
    html_content = f"""
    <html>
    <head>
        <title>Logistics Dashboard - Neuronova</title>
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: white; padding: 40px; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
            h1 {{ color: #38bdf8; margin-bottom: 32px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
            th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #334155; }}
            th {{ color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; }}
            .status {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; background: #065f46; color: #34d399; }}
            .metric {{ font-size: 1.5rem; font-weight: bold; color: #38bdf8; }}
        </style>
    </head>
    <body>
        <h1>🚀 Logistics Optimization Dashboard</h1>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;">
            <div class="card">
                <p>Weather Status</p>
                <div class="metric">{weather if weather else "Clear"}</div>
            </div>
            <div class="card">
                <p>Total Vehicles</p>
                <div class="metric">{len(routes)}</div>
            </div>
            <div class="card">
                <p>Optimization Priority</p>
                <div class="metric">Balanced</div>
            </div>
        </div>

        <div class="card">
            <h2>Vehicle Utilization</h2>
            <table>
                <thead>
                    <tr>
                        <th>Vehicle</th>
                        <th>Profile</th>
                        <th>Distance</th>
                        <th>Duration</th>
                        <th>Stops</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for route in routes:
        html_content += f"""
                    <tr>
                        <td>Vehicle {route['vehicle']}</td>
                        <td>{route['vehicle_name']}</td>
                        <td>{route['distance']:.1f}m</td>
                        <td>{route['time']:.0f}s</td>
                        <td>{len(route['sequence'])-2}</td>
                        <td><span class="status">Optimized</span></td>
                    </tr>
        """
        
    html_content += """
                </tbody>
            </table>
        </div>
        <div style="text-align: center; color: #64748b; font-size: 0.875rem;">
            Generated by Antigravity Delivery Optimizer v2.0
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    logger.info(f"Logistics Dashboard saved to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Neuronova Delivery Optimizer")
    parser.add_argument("--city", type=str, default="berlin", help="City profile to use")
    parser.add_argument("--mock", action="store_true", help="Generate mock data")
    args = parser.parse_args()

    # Update global config for this run
    import city_configs
    profile = city_configs.get_city_profile(args.city)
    config.FALLBACK_SPEED_KMH = profile["avg_speed_kmh"]
    
    logger.info(f"Starting {profile['name']} Delivery Optimizer...")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    if args.mock:
        logger.info(f"Generating mock data for {args.city}...")
        df = data_utils.generate_mock_data(profile)
    else:
        file_path = os.path.join(base_dir, 'data', 'locations.csv')
        logger.info(f"Loading data from {file_path}...")
        df = data_utils.load_data_from_csv(file_path)
    if df is None: return

    print("Delivery Locations:")
    print(df[['id', 'demand', 'priority']])
    
    # 2. Get Distance/Time Matrix
    logger.info("Fetching distance/time matrix...")
    start_time = time.time()
    dist_matrix, time_matrix = data_utils.get_tomtom_matrix(df)
    fetch_duration = time.time() - start_time
    logger.info(f"Data acquisition took {fetch_duration:.2f} seconds.")

    # 3. Apply Weather
    depot = df.iloc[config.DEPOT_INDEX]
    weather_condition = data_utils.get_current_weather(depot['lat'], depot['lon'])
    if weather_condition:
        time_matrix = data_utils.apply_weather_impact(time_matrix, weather_condition)
    else:
        logger.info("Proceeding without real-time weather adjustments.")

    # 4. Optimize
    logger.info("Running Optimizer...")
    optimizer = RouteOptimizer(df, dist_matrix, time_matrix)
    solution = optimizer.solve()
    
    if solution:
        routes = optimizer.print_solution()
        
        # 5. Visualization & Reporting
        map_path = os.path.join(output_dir, "route_map.html")
        report_path = os.path.join(output_dir, "logistics_report.html")
        
        visualize_route(df, routes, filename=map_path)
        generate_logistics_dashboard(routes, weather_condition, report_path)
        
        logger.info("\n--- Simulating Dynamic Trigger ---")
        # Simulate a delay or traffic change to test the trigger
        # Assume initial estimated time for Route 0 is T_est
        if routes:
            initial_eta = routes[0]['time']
            
            # Scenario: Major delay (20%)
            logger.info("Scenario: Major delay (20%)")
            new_eta_major = initial_eta * 1.20
            if check_reoptimization(new_eta_major, initial_eta):
                logger.info(">> RE-OPTIMIZE TRIGGERED!")
            else:
                logger.info(">> Variance within limits. No action.")
                
    else:
        logger.error("Failed to find a solution.")

if __name__ == "__main__":
    main()
