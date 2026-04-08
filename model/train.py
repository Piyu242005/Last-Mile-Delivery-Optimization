"""
model/train.py
--------------
Trains models (Linear Regression, Random Forest, XGBoost) to predict
delivery time based on features like distance, time of day, etc.
Saves the best model for the API.
"""

import json
import joblib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "processed_sample.parquet"
MODEL_PATH = ROOT / "model" / "best_model.pkl"
METRICS_PATH = ROOT / "model" / "metrics.json"

FEATURES = [
    "haversine_km",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "speed_mph"  # Proxy for traffic level (we'll ask user for traffic estimate in UI)
]
TARGET = "trip_duration_mins"


def main(subset: int = None):
    print("Loading data...")
    df = pd.read_parquet(DATA_PATH)
    
    if subset:
        print(f"Subsampling to {subset} rows for faster training...")
        df = df.sample(subset, random_state=42)

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Training on {len(X_train)} rows, testing on {len(X_test)} rows.\n")

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=50, max_depth=10, n_jobs=-1, random_state=42),
        "XGBoost": xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, n_jobs=-1, random_state=42)
    }

    results = {}
    best_model_name = None
    best_rmse = float('inf')
    best_model_instance = None

    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = r2_score(y_test, preds)
        
        results[name] = {"RMSE_mins": round(rmse, 2), "R2": round(r2, 3)}
        print(f"  → RMSE: {rmse:.2f} mins | R²: {r2:.3f}")

        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            best_model_instance = model

    print(f"\n🏆 Best Model: {best_model_name} (RMSE: {best_rmse:.2f})")
    
    # Save the best model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model_instance, MODEL_PATH)
    print(f"Saved best model to {MODEL_PATH}")

    # Save metrics
    with open(METRICS_PATH, "w") as f:
        json.dump({"best_model": best_model_name, "results": results}, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=int, default=100_000, 
                        help="Number of rows to train on (for speed)")
    args = parser.parse_args()
    main(subset=args.subset)
