from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from model.route_optimizer import solve_vrp
import uvicorn
import math

app = FastAPI(title="Last Mile Delivery API")

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
    # Dummy mock prediction returning formula based result for UI demonstration
    # Since we lack the trained XGBoost model here.
    base_time = (req.trip_distance / req.speed_mph) * 60
    traffic_modifier = 1.0 + (math.sin(req.hour_of_day/24 * math.pi) * 0.5)
    total_mins = round(base_time * traffic_modifier, 2)
    return {"predicted_duration_mins": total_mins}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
