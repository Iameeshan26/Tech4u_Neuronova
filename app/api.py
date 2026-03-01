from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import uuid
import pandas as pd
import data_utils
import config
from optimizer import RouteOptimizer
import os
import logging

app = FastAPI(title="Neuronova Delivery Optimizer API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory job storage (for demo purposes)
# In production, use Redis/PostgreSQL
jobs = {}

class Location(BaseModel):
    id: str
    lat: float
    lon: float
    demand: int
    priority: int

class OptimizeRequest(BaseModel):
    locations: list[Location]

@app.get("/")
async def root():
    return {"message": "Neuronova Delivery Optimizer API is running."}

@app.post("/optimize")
async def optimize(request: OptimizeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "result": None}
    
    background_tasks.add_task(process_optimization, job_id, request.locations)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

async def process_optimization(job_id: str, locations: list[Location]):
    try:
        # Convert to DataFrame
        data = [loc.dict() for loc in locations]
        df = pd.DataFrame(data)
        
        # Get Matrix
        points = [(loc.lat, loc.lon) for loc in locations]
        dist_matrix, time_matrix = data_utils.get_tomtom_matrix_from_points(points)
        
        # Apply Weather (Depot weather)
        weather_condition = data_utils.get_current_weather(locations[0].lat, locations[0].lon)
        if weather_condition:
            time_matrix = data_utils.apply_weather_impact(time_matrix, weather_condition)
        
        # Run Optimizer
        optimizer = RouteOptimizer(df, dist_matrix, time_matrix)
        solution = optimizer.solve()
        
        if solution:
            routes = optimizer.print_solution()
            jobs[job_id] = {
                "status": "completed",
                "result": {
                    "routes": routes,
                    "total_distance": sum(r['distance'] for r in routes),
                    "total_time": sum(r['time'] for r in routes),
                    "weather": weather_condition
                }
            }
        else:
            jobs[job_id] = {"status": "failed", "error": "No solution found"}
            
    except Exception as e:
        logger.error(f"Error in background task: {e}")
        jobs[job_id] = {"status": "failed", "error": str(e)}

@app.get("/map/{job_id}", response_class=HTMLResponse)
async def get_map(job_id: str):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="Map not ready or job not found")
    
    root_dir = os.path.dirname(os.path.dirname(__file__))
    map_path = os.path.join(root_dir, "output", f"map_{job_id}.html")
    
    if not os.path.exists(map_path):
        return HTMLResponse(content="<html><body><h1>Map Generation in Progress...</h1><p>Please refresh in a moment.</p></body></html>")

    with open(map_path, "r") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
