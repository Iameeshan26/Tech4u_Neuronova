from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uuid
import db_store
import os
import logging
import data_utils
import pandas as pd

app = FastAPI(title="Neuronova Pro API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Location(BaseModel):
    id: str
    lat: float
    lon: float
    demand: int
    priority: int

class OptimizeRequest(BaseModel):
    locations: list[Location]
    city: str = "berlin"

@app.get("/")
async def root():
    return {"message": "Neuronova Pro API is running (Asynchronous Worker Mode)."}

@app.get("/locations")
async def get_initial_locations():
    """Serves the base delivery locations from CSV."""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(root_dir, 'data', 'locations.csv')
    try:
        df = data_utils.load_data_from_csv(file_path)
        if df is not None:
            return df.to_dict('records')
        return []
    except Exception as e:
        logger.error(f"Failed to load locations: {e}")
        return []

@app.post("/optimize")
async def optimize(request: OptimizeRequest):
    # Pro-Level: Instant Response (Sub-10ms)
    job_id = str(uuid.uuid4())
    
    # Store in persistent DB
    db_store.add_job(
        job_id, 
        request.city, 
        [loc.dict() for loc in request.locations]
    )
    
    logger.info(f"Job {job_id} queued for city {request.city}")
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = db_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/map/{job_id}", response_class=HTMLResponse)
async def get_map(job_id: str):
    job = db_store.get_job(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Map not ready or job not found")
    
    root_dir = os.path.dirname(os.path.dirname(__file__))
    map_path = os.path.join(root_dir, "output", f"map_{job_id}.html")
    
    if not os.path.exists(map_path):
        return HTMLResponse(content="<html><body><h1>Map Rendering in Progress...</h1><p>The worker is still generating visual assets.</p></body></html>")

    with open(map_path, "r") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
