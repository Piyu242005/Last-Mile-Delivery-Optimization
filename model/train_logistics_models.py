"""Train optional logistics intelligence models from a historical delivery CSV.

Usage:
    python model/train_logistics_models.py --csv data/deliveries.csv

Expected columns can include:
    distance_km, hour, traffic_factor, demand, route_load_ratio,
    duration_mins, late (0/1), date
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
FEATURES = ["distance_km", "hour", "traffic_factor", "demand", "route_load_ratio"]


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    defaults = {"distance_km": 5.0, "hour": 14, "traffic_factor": 1.0, "demand": 1, "route_load_ratio": 0.5}
    for col, value in defaults.items():
        if col not in out:
            out[col] = value
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(value)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    df = prepare(pd.read_csv(args.csv))
    MODEL_DIR.mkdir(exist_ok=True)
    X = df[FEATURES]
    train, test = train_test_split(df, test_size=0.2, random_state=42)

    if "duration_mins" in df:
        model = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, objective="reg:squarederror", random_state=42)
        model.fit(train[FEATURES], train["duration_mins"])
        pred = model.predict(test[FEATURES])
        print(f"ETA MAE: {mean_absolute_error(test['duration_mins'], pred):.3f}")
        print(f"ETA R2: {r2_score(test['duration_mins'], pred):.3f}")
        joblib.dump(model, MODEL_DIR / "eta_xgb.pkl")

    if "late" in df:
        model = XGBClassifier(n_estimators=250, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, eval_metric="logloss", random_state=42)
        model.fit(train[FEATURES], train["late"].astype(int))
        pred = model.predict(test[FEATURES])
        print(f"Late-risk accuracy: {accuracy_score(test['late'], pred):.3f}")
        joblib.dump(model, MODEL_DIR / "late_risk_xgb.pkl")

    print("Models saved to model/")


if __name__ == "__main__":
    main()
