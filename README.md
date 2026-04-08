# 🚚 Last Mile Delivery Optimization System

A scalable logistics and Last-Mile Delivery optimization system built on top of a 50GB NYC Taxi dataset. The system ingests dispatch coordinates, trains a Machine Learning model to predict delivery times, and provides a routing engine to optimize delivery vehicle paths.

> **Why NYC Taxi Data?**  
> We treat taxi pickups as "warehouse dispatches" and drop-offs as "delivery destinations" to simulate a dense, real-world urban logistics network.

---

## 🎯 Architecture & Features

The project is structured into three main components:

1. **Machine Learning Pipeline (XGBoost Regressor)**
   - Chunk-reads massive CSV datasets (`data/preprocess.py`) to bypass RAM limits.
   - Engineers features (Haversine distance, speed mapping, traffic estimation, day/time).
   - Trains an XGBoost model (`model/train.py`) achieving ~2.98 mins RMSE.
2. **Route Optimizer (Google OR-Tools)**
   - Formulates delivery stops as a Vehicle Routing Problem (VRP).
   - Generates the shortest path connecting a depot to all requested delivery stops.
3. **Interactive UI & API (FastAPI + Streamlit)**
   - **Backend**: FastAPI serves the ML predictions and Route Optimization logic.
   - **Frontend**: Streamlit provides KPI cards, dynamic Folium maps, and a live prediction form.

---

## 🚀 Setup & Execution

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Process Data & Train Model
*Requires the raw CSVs in the `Dataset/` folder.*
```bash
# Processes the CSVs in 100k-row chunks, cleaning and feature-engineering
python data/preprocess.py

# Trains the XGBoost model and saves the weights
python model/train.py
```

### 3. Start the Backend API
In terminal 1:
```bash
uvicorn api.main:app --reload
```
*API will run on `http://localhost:8000` with Swagger Docs at `http://localhost:8000/docs`.*

### 4. Start the Dashboard UI
In terminal 2:
```bash
streamlit run dashboard/app.py
```
*Dashboard will run on `http://localhost:8501`.*

---

## 📸 System Overview

*   **Prediction Accuracy:** Achieved an **RMSE of 2.98 mins** on out-of-sample data.
*   **Scalability Check:** The `data/preprocess.py` pipeline is designed using standard data-engineering chunk reading to handle 50GB+ workloads on standard consumer hardware.
*   **Routing Execution:** The OR-Tools engine solves up to 50 local stops in < 2 seconds.

---

### 💼 Resume Highlight
> *Built a scalable last-mile delivery optimization system processing large datasets, improving delivery time estimations using XGBoost and optimizing delivery routes using Google OR-Tools and FastAPI.*
