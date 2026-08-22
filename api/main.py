import math
from pathlib import Path
from typing import List, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from model.route_optimizer import solve_vrp

app = FastAPI(title="Last Mile Delivery Optimization API", version="1.1.0")
MODEL_PATH = Path(__file__).parent.parent / "model" / "best_model.pkl"

try:
    eta_model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
    MODEL_LOAD_ERROR = None
except Exception as exc:
    eta_model = None
    MODEL_LOAD_ERROR = str(exc)


class Coordinates(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RouteRequest(BaseModel):
    depot: Coordinates
    stops: List[Coordinates] = Field(min_length=1)
    num_vehicles: int = Field(default=1, ge=1, le=100)
    demands: Optional[List[int]] = None
    vehicle_capacities: Optional[List[int]] = None
    traffic_factor: float = Field(default=1.0, gt=0, le=10)

    @model_validator(mode="after")
    def validate_lengths(self):
        if self.demands is not None and len(self.demands) != len(self.stops) + 1:
            raise ValueError("demands must contain depot demand plus one demand per stop")
        if self.vehicle_capacities is not None and len(self.vehicle_capacities) != self.num_vehicles:
            raise ValueError("vehicle_capacities must contain one value per vehicle")
        return self


class PredictRequest(BaseModel):
    trip_distance: float = Field(gt=0)
    haversine_km: float = Field(gt=0)
    hour_of_day: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    is_weekend: int = Field(ge=0, le=1)
    speed_mph: float = Field(gt=0)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "eta_model_loaded": eta_model is not None,
        "model_load_error": MODEL_LOAD_ERROR,
    }


@app.post("/optimize-route")
def optimize_route(req: RouteRequest):
    try:
        return solve_vrp(
            depot_coords=(req.depot.lat, req.depot.lon),
            stops_coords=[(stop.lat, stop.lon) for stop in req.stops],
            num_vehicles=req.num_vehicles,
            vehicle_capacities=req.vehicle_capacities,
            demands=req.demands,
            traffic_factor=req.traffic_factor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Route optimization failed.") from exc


@app.post("/predict")
def predict_duration(req: PredictRequest):
    if eta_model is not None:
        features = pd.DataFrame([{
            "haversine_km": req.haversine_km,
            "hour_of_day": req.hour_of_day,
            "day_of_week": req.day_of_week,
            "is_weekend": req.is_weekend,
            "speed_mph": req.speed_mph,
        }])
        prediction = eta_model.predict(features)[0]
        return {"predicted_duration_mins": round(float(prediction), 2), "model_used": "trained_model"}

    base_time = (req.trip_distance / req.speed_mph) * 60
    traffic_modifier = 1.0 + (math.sin(req.hour_of_day / 24 * math.pi) * 0.5)
    total_mins = round(base_time * traffic_modifier, 2)
    return {"predicted_duration_mins": total_mins, "model_used": "analytical_fallback"}
