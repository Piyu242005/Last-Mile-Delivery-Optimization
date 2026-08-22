"""Train ETA models with a time-aware validation split."""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "processed_sample.parquet"
MODEL_PATH = ROOT / "model" / "best_model.pkl"
METRICS_PATH = ROOT / "model" / "metrics.json"
FEATURES = ["haversine_km", "hour_of_day", "day_of_week", "is_weekend", "speed_mph"]
TARGET = "trip_duration_mins"


def time_split(df):
    """Sort chronologically and reserve the newest 20% as an unseen test set."""
    if "pickup_datetime" in df.columns:
        df = df.sort_values("pickup_datetime").reset_index(drop=True)
    else:
        df = df.sort_index().reset_index(drop=True)
    split = max(1, int(len(df) * 0.8))
    return df.iloc[:split], df.iloc[split:]


def main(subset: int = 100_000):
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Processed dataset not found: {DATA_PATH}")

    df = pd.read_parquet(DATA_PATH).dropna(subset=FEATURES + [TARGET]).copy()
    if subset and subset < len(df):
        df = df.tail(subset).copy()

    train_df, test_df = time_split(df)
    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42),
        "XGBoost": xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, n_jobs=-1, random_state=42),
    }

    results = {}
    best_name = None
    best_rmse = float("inf")
    best_model = None

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        results[name] = {"MAE_mins": round(mae, 2), "RMSE_mins": round(rmse, 2), "R2": round(r2, 3)}
        if rmse < best_rmse:
            best_name, best_rmse, best_model = name, rmse, model

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    with METRICS_PATH.open("w", encoding="utf-8") as handle:
        json.dump({
            "validation_method": "chronological 80/20 split",
            "train_rows": len(train_df),
            "test_rows": len(test_df),
            "best_model": best_name,
            "results": results,
        }, handle, indent=2)
    print(f"Best model: {best_name} | RMSE: {best_rmse:.2f} mins")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=int, default=100_000)
    main(subset=parser.parse_args().subset)
