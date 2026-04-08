"""
data/preprocess.py
------------------
Reads NYC Yellow Taxi CSVs in chunks (demonstrating 50 GB+ scalability),
engineers delivery-relevant features, and saves a processed Parquet sample.
"""

import os
import glob
import json
import math
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "Dataset"
OUT_DIR = ROOT / "data"
OUT_PARQUET = OUT_DIR / "processed_sample.parquet"
STATS_JSON = OUT_DIR / "dataset_stats.json"

CHUNKSIZE = 100_000          # rows per chunk  (shows large-data strategy)
SAMPLE_ROWS = 500_000        # rows to keep in processed sample


# ── Haversine distance ────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    """Return great-circle distance in km (vectorised, numpy)."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


# ── Traffic level from speed ──────────────────────────────────────────────────
def traffic_level(speed_mph):
    conditions = [speed_mph < 10, speed_mph < 20, speed_mph < 30]
    choices = ["Heavy", "Moderate", "Light"]
    return np.select(conditions, choices, default="Free-flow")


# ── Process a single chunk ────────────────────────────────────────────────────
def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    # Rename columns for clarity (handle both 2015 and 2016 schemas)
    col_map = {
        "tpep_pickup_datetime": "pickup_dt",
        "tpep_dropoff_datetime": "dropoff_dt",
        "pickup_longitude": "pickup_lon",
        "pickup_latitude": "pickup_lat",
        "dropoff_longitude": "dropoff_lon",
        "dropoff_latitude": "dropoff_lat",
    }
    chunk = chunk.rename(columns={k: v for k, v in col_map.items() if k in chunk.columns})

    # ── Parse datetimes ──
    for col in ["pickup_dt", "dropoff_dt"]:
        chunk[col] = pd.to_datetime(chunk[col], errors="coerce")

    # ── Drop rows with null coords / datetimes ──
    required = ["pickup_dt", "dropoff_dt", "pickup_lat", "pickup_lon",
                "dropoff_lat", "dropoff_lon", "trip_distance"]
    chunk = chunk.dropna(subset=[c for c in required if c in chunk.columns])

    # ── Bounding-box filter (NYC area) ──
    chunk = chunk[
        chunk["pickup_lat"].between(40.4, 41.0) &
        chunk["pickup_lon"].between(-74.3, -73.6) &
        chunk["dropoff_lat"].between(40.4, 41.0) &
        chunk["dropoff_lon"].between(-74.3, -73.6)
    ]

    # ── Feature engineering ──
    chunk["trip_duration_mins"] = (
        (chunk["dropoff_dt"] - chunk["pickup_dt"]).dt.total_seconds() / 60
    )
    # Valid duration: 1 min – 3 hrs
    chunk = chunk[chunk["trip_duration_mins"].between(1, 180)]
    chunk = chunk[chunk["trip_distance"] > 0]

    chunk["haversine_km"] = haversine(
        chunk["pickup_lat"].values, chunk["pickup_lon"].values,
        chunk["dropoff_lat"].values, chunk["dropoff_lon"].values,
    )

    chunk["hour_of_day"] = chunk["pickup_dt"].dt.hour
    chunk["day_of_week"] = chunk["pickup_dt"].dt.dayofweek   # 0=Mon
    chunk["is_weekend"] = (chunk["day_of_week"] >= 5).astype(int)
    chunk["month"] = chunk["pickup_dt"].dt.month

    chunk["speed_mph"] = (chunk["trip_distance"] / (chunk["trip_duration_mins"] / 60)).clip(0, 80)
    chunk["traffic_level"] = traffic_level(chunk["speed_mph"].values)

    # Keep only useful columns
    keep = [
        "pickup_dt", "pickup_lat", "pickup_lon",
        "dropoff_lat", "dropoff_lon",
        "trip_distance", "haversine_km",
        "trip_duration_mins", "speed_mph",
        "hour_of_day", "day_of_week", "is_weekend", "month",
        "traffic_level",
        "passenger_count", "fare_amount",
    ]
    keep = [c for c in keep if c in chunk.columns]
    return chunk[keep].reset_index(drop=True)


# ── Main processing loop ──────────────────────────────────────────────────────
def run(sample_only: bool = False):
    csv_files = sorted(glob.glob(str(DATA_DIR / "yellow_tripdata_*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

    print(f"Found {len(csv_files)} CSV file(s). Processing in chunks of {CHUNKSIZE:,}…")

    frames = []
    total_raw = 0
    total_clean = 0

    for csv_path in csv_files:
        fname = os.path.basename(csv_path)
        print(f"\n  → {fname}")
        for i, chunk in enumerate(pd.read_csv(csv_path, chunksize=CHUNKSIZE, low_memory=False)):
            total_raw += len(chunk)
            processed = process_chunk(chunk)
            total_clean += len(processed)
            frames.append(processed)
            rows_so_far = sum(len(f) for f in frames)
            print(f"     chunk {i+1:3d} | raw {len(chunk):>7,} | clean {len(processed):>7,} "
                  f"| cumulative clean {rows_so_far:>9,}", end="\r")
            if rows_so_far >= SAMPLE_ROWS:
                break
        if sum(len(f) for f in frames) >= SAMPLE_ROWS:
            break
        if sample_only:
            break

    df = pd.concat(frames, ignore_index=True).head(SAMPLE_ROWS)
    print(f"\n\nProcessing complete → {len(df):,} clean rows (from {total_raw:,} raw rows scanned)")
    print(f"Clean rate: {100 * total_clean / max(total_raw, 1):.1f}%")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"Saved → {OUT_PARQUET}")

    # Save stats for the dashboard
    stats = {
        "total_rows": len(df),
        "avg_duration_mins": round(df["trip_duration_mins"].mean(), 2),
        "avg_distance_km": round(df["haversine_km"].mean(), 2),
        "avg_speed_mph": round(df["speed_mph"].mean(), 2),
        "date_range_start": str(df["pickup_dt"].min()),
        "date_range_end": str(df["pickup_dt"].max()),
    }
    with open(STATS_JSON, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Stats → {STATS_JSON}")
    print("\nSample stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-only", action="store_true",
                        help="Process only the first file (fast test)")
    args = parser.parse_args()
    run(sample_only=args.sample_only)
