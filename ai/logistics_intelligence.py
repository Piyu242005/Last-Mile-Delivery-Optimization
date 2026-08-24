"""AI intelligence layer for last-mile logistics.

Provides lightweight, production-friendly feature engineering and scoring
utilities that can be used by the Streamlit dashboard or FastAPI service.
Trained models can be plugged in through joblib artifacts.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"


@dataclass
class DeliveryRisk:
    score: float
    label: str
    reasons: list[str]


def _load(name: str):
    path = MODEL_DIR / name
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def delivery_risk(distance_km: float, hour: int, traffic_factor: float,
                  demand: float = 1, route_load_ratio: float = 0.5) -> DeliveryRisk:
    """Return an interpretable late-delivery risk score (0-100).

    If a trained classifier artifact is available it can be used by the API;
    otherwise this deterministic baseline remains useful and transparent.
    """
    score = 15.0
    reasons: list[str] = []
    if distance_km > 10:
        score += 22; reasons.append("long route")
    if 7 <= hour <= 10 or 16 <= hour <= 19:
        score += 20; reasons.append("peak-hour traffic")
    if traffic_factor >= 1.5:
        score += 25; reasons.append("heavy traffic")
    elif traffic_factor >= 1.25:
        score += 12; reasons.append("moderate traffic")
    if route_load_ratio >= 0.85:
        score += 15; reasons.append("high vehicle utilization")
    if demand >= 8:
        score += 8; reasons.append("large delivery demand")
    score = min(100.0, round(score, 1))
    label = "HIGH" if score >= 65 else "MEDIUM" if score >= 35 else "LOW"
    return DeliveryRisk(score, label, reasons or ["normal operating conditions"])


def fleet_assignment_score(distance_km: float, vehicle_load_ratio: float,
                           vehicle_capacity_ratio: float, traffic_factor: float) -> float:
    """Lower score is better for assigning an order to a vehicle."""
    return round(
        distance_km * 0.55
        + vehicle_load_ratio * 30
        + vehicle_capacity_ratio * 10
        + max(0, traffic_factor - 1) * 15,
        3,
    )


def demand_forecast(history: pd.DataFrame, periods: int = 7) -> pd.DataFrame:
    """Simple robust baseline forecast using recent-day demand trend.

    Expected columns: date and demand. This is intentionally dependency-light
    and can later be replaced by a LightGBM/XGBoost time-series model.
    """
    if history.empty or "demand" not in history:
        raise ValueError("history must contain a demand column")
    values = pd.to_numeric(history["demand"], errors="coerce").dropna()
    if values.empty:
        raise ValueError("demand column contains no numeric values")
    window = values.tail(min(14, len(values)))
    if len(window) >= 2:
        slope = np.polyfit(np.arange(len(window)), window.to_numpy(), 1)[0]
    else:
        slope = 0.0
    base = float(window.mean())
    future = [max(0.0, base + slope * (i + 1)) for i in range(periods)]
    start = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    return pd.DataFrame({"date": pd.date_range(start, periods=periods), "forecast_demand": np.round(future, 2)})


def copilot_context(route_data: dict[str, Any] | None) -> dict[str, Any]:
    """Convert an optimization result into concise facts for an LLM copilot."""
    if not route_data or not route_data.get("routes"):
        return {"status": "no_route"}
    routes = route_data["routes"]
    return {
        "status": "optimized",
        "vehicles": len(routes),
        "total_distance_km": route_data.get("total_distance_km"),
        "baseline_distance_km": route_data.get("baseline_distance_km"),
        "saved_distance_km": route_data.get("saved_distance_km"),
        "efficiency_improvement_pct": route_data.get("efficiency_improvement_pct"),
        "vehicle_loads": [r.get("load", 0) for r in routes],
        "vehicle_distances_km": [r.get("distance_km", 0) for r in routes],
    }
