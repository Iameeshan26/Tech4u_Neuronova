import time
import json
import logging
import db_store
import data_utils
import config
import city_configs
from optimizer import RouteOptimizer
import pandas as pd
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - WORKER - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_worker():
    logger.info("Neuronova Optimization Worker started. Polling for jobs...")
    
    while True:
        job = db_store.get_next_job()
        if not job:
            time.sleep(2)
            continue
            
        job_id, city, payload_json = job
        logger.info(f"Processing Job {job_id} for city: {city}")
        
        try:
            locations_data = json.loads(payload_json)
            df = pd.DataFrame(locations_data)
            
            # Load Profile
            profile = city_configs.get_city_profile(city)
            config.FALLBACK_SPEED_KMH = profile["avg_speed_kmh"]
            
            # Get Matrix (Now with IDM integration ideally)
            points = [(loc['lat'], loc['lon']) for loc in locations_data]
            dist_matrix, time_matrix = data_utils.get_tomtom_matrix_from_points(points)
            
            # Apply Weather & Seasonality
            weather_condition = data_utils.get_current_weather(locations_data[0]['lat'], locations_data[0]['lon'])
            if weather_condition:
                time_matrix = data_utils.apply_weather_impact(time_matrix, weather_condition)
            
            # Run Optimizer
            optimizer = RouteOptimizer(df, dist_matrix, time_matrix)
            solution = optimizer.solve()
            
            if solution:
                routes = optimizer.print_solution()
                # Ensure distance/time are JSON serializable (standard float)
                result = {
                    "routes": routes,
                    "total_distance": float(sum(r['distance'] for r in routes)),
                    "total_time": float(sum(r['time'] for r in routes)),
                    "weather": weather_condition,
                    "city": city
                }
                db_store.update_job_status(job_id, "completed", result=result)
                logger.info(f"Job {job_id} finished successfully.")
            else:
                db_store.update_job_status(job_id, "failed", error="No solution found.")
                
        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")
            db_store.update_job_status(job_id, "failed", error=str(e))

if __name__ == "__main__":
    run_worker()
