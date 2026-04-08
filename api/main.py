"""
api/main.py
-----------
FastAPI app exposing endpoints for delivery time prediction and route optimization.
"""

import sys
import joblib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist

# We need to import route_optimizer from the parent directory
sys.path.append(str(Path(__file__).parent.parent))
from model.route_optimizer import solve_vrp

app = FastAPI(title="Last Mile Delivery API")

MODEL_PATH = Path(__file__).parent.parent / "model" / "best_model.pkl"

# Load the model at startup
try:
    model = joblib.load(MODEL_PATH)
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    model = None

# --- Schemas ---
class PredictionRequest(BaseModel):
    trip_distance: float
    haversine_km: float
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    speed_mph: float

class Point(BaseModel):
    lat: float
    lon: float

class RouteOptimizationRequest(BaseModel):
    depot: Point
    stops: conlist(Point, min_length=1, max_length=50) # type: ignore
    num_vehicles: int = 1

# --- Endpoints ---
@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
def predict_delivery_time(req: PredictionRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Feature order must match training data
    features = [[
        req.haversine_km,
        req.hour_of_day,
        req.day_of_week,
        req.is_weekend,
        req.speed_mph
    ]]
    
    try:
        duration_mins = model.predict(features)[0]
        return {"predicted_duration_mins": round(float(duration_mins), 2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/optimize-route")
def optimize_route(req: RouteOptimizationRequest):
    depot_tuple = (req.depot.lat, req.depot.lon)
    stops_list = [(stop.lat, stop.lon) for stop in req.stops]
    
    try:
        result = solve_vrp(depot_tuple, stops_list, num_vehicles=req.num_vehicles)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
