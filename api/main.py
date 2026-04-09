from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from model.route_optimizer import solve_vrp
import uvicorn
import math
import joblib
import pandas as pd
from pathlib import Path

app = FastAPI(title="Last Mile Delivery API")

MODEL_PATH = Path(__file__).parent.parent / "model" / "best_model.pkl"
try:
    eta_model = joblib.load(MODEL_PATH)
except:
    eta_model = None

class Coordinates(BaseModel):
    lat: float
    lon: float

class RouteRequest(BaseModel):
    depot: Coordinates
    stops: List[Coordinates]
    num_vehicles: int = 1
    demands: List[int] = None
    vehicle_capacities: List[int] = None
    traffic_factor: float = 1.0

@app.post("/optimize-route")
def optimize_route(req: RouteRequest):
    depot_tuple = (req.depot.lat, req.depot.lon)
    stops_tuples = [(stop.lat, stop.lon) for stop in req.stops]
    
    result = solve_vrp(
        depot_coords=depot_tuple, 
        stops_coords=stops_tuples,
        num_vehicles=req.num_vehicles,
        vehicle_capacities=req.vehicle_capacities,
        demands=req.demands,
        traffic_factor=req.traffic_factor
    )
    return result

class PredictRequest(BaseModel):
    trip_distance: float
    haversine_km: float
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    speed_mph: float

@app.post("/predict")
def predict_duration(req: PredictRequest):
    if eta_model:
        # Advanced ML logic Using pre-trained XGBoost / RF Regressor
        features = pd.DataFrame([{
            "haversine_km": req.haversine_km,
            "hour_of_day": req.hour_of_day,
            "day_of_week": req.day_of_week,
            "is_weekend": req.is_weekend,
            "speed_mph": req.speed_mph
        }])
        pred = eta_model.predict(features)[0]
        return {"predicted_duration_mins": round(float(pred), 2), "model_used": "XGBoost/RF"}
    else:
        # Fallback to analytical calculation if model not yet trained
        base_time = (req.trip_distance / req.speed_mph) * 60
        traffic_modifier = 1.0 + (math.sin(req.hour_of_day/24 * math.pi) * 0.5)
        total_mins = round(base_time * traffic_modifier, 2)
        return {"predicted_duration_mins": total_mins, "model_used": "Analytical Fallback"}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
