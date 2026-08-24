from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])
ROOT = Path(__file__).parent.parent
AI_DIR = ROOT / "ai"

try:
    from ai.logistics_intelligence import LogisticsIntelligence
    intelligence = LogisticsIntelligence(AI_DIR)
except Exception:
    intelligence = None


class RiskRequest(BaseModel):
    distance_km: float = Field(gt=0)
    hour_of_day: int = Field(ge=0, le=23)
    traffic_factor: float = Field(gt=0, le=10)
    demand: int = Field(ge=0)
    vehicle_capacity: int = Field(gt=0)


class DemandRequest(BaseModel):
    historical_demand: list[float] = Field(min_length=3, max_length=365)
    horizon: int = Field(default=7, ge=1, le=30)


class CopilotRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    context: dict = {}


@router.get("/status")
def ai_status():
    return {"available": intelligence is not None, "modules": ["eta", "late_risk", "demand_forecast", "vehicle_scoring", "copilot"]}


@router.post("/late-risk")
def late_risk(req: RiskRequest):
    if intelligence is None:
        raise HTTPException(status_code=503, detail="AI intelligence module unavailable")
    return intelligence.late_delivery_risk(req.model_dump())


@router.post("/demand-forecast")
def demand_forecast(req: DemandRequest):
    if intelligence is None:
        raise HTTPException(status_code=503, detail="AI intelligence module unavailable")
    return intelligence.forecast_demand(req.historical_demand, req.horizon)


@router.post("/vehicle-score")
def vehicle_score(payload: dict):
    if intelligence is None:
        raise HTTPException(status_code=503, detail="AI intelligence module unavailable")
    return intelligence.score_vehicles(payload.get("vehicles", []), payload.get("order", {}))


@router.post("/copilot")
def copilot(req: CopilotRequest):
    if intelligence is None:
        raise HTTPException(status_code=503, detail="AI intelligence module unavailable")
    return intelligence.copilot(req.question, req.context)
