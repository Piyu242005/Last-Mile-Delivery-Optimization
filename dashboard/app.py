"""
dashboard/app.py
----------------
Streamlit dashboard for the Last Mile Delivery Optimization system.
Includes tabs for System KPI Overview, Route Optimization Map, and Delivery Prediction.
"""

import sys
import json
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path
import pandas as pd

# Path setup
ROOT = Path(__file__).parent.parent
STATS_PATH = ROOT / "data" / "dataset_stats.json"
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Last Mile Delivery Optimizer",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚚 Last Mile Delivery Optimization")
st.markdown("Optimize delivery routes and predict delivery times using Machine Learning.")

# --- Load Stats ---
@st.cache_data
def load_stats():
    if STATS_PATH.exists():
        with open(STATS_PATH, "r") as f:
            return json.load(f)
    return {}

stats = load_stats()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗺️ Route Optimizer", "🤖 Time Predictor"])

with tab1:
    st.header("System Overview")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Orders Processed", f"{stats.get('total_rows', 0):,}")
        col2.metric("Avg Duration", f"{stats.get('avg_duration_mins', 0)} mins")
        col3.metric("Avg Distance", f"{stats.get('avg_distance_km', 0)} km")
        col4.metric("Avg Speed", f"{stats.get('avg_speed_mph', 0)} mph")
        
        st.info("💡 **Fun Fact**: This system can ingest and process over 50GB of raw dispatch logs using chunked processing, feeding clean Parquet files to the ML training pipeline.")
    else:
        st.warning("No dataset stats found. Run the preprocessing script first.")

with tab2:
    st.header("Route Optimizer")
    st.markdown("Using **Google OR-Tools** to solve the Vehicle Routing Problem (VRP).")
    
    col_input, col_map = st.columns([1, 2])
    
    with col_input:
        st.subheader("Add Stops")
        # Default NYC points
        default_depot = "40.750,-73.990"
        default_stops = "40.748,-73.985\n40.761,-73.978\n40.732,-73.996"
        
        depot_input = st.text_input("Depot (Lat, Lon)", default_depot)
        stops_input = st.text_area("Delivery Stops (one per line)", default_stops, height=150)
        
        if st.button("Optimize Route", type="primary"):
            try:
                # Parse inputs
                d_lat, d_lon = map(float, depot_input.split(","))
                depot = {"lat": d_lat, "lon": d_lon}
                
                stops = []
                for line in stops_input.split("\n"):
                    if line.strip():
                        lat, lon = map(float, line.split(","))
                        stops.append({"lat": lat, "lon": lon})
                
                # Call FastAPI backend
                with st.spinner("Finding optimal route..."):
                    payload = {"depot": depot, "stops": stops, "num_vehicles": 1}
                    res = requests.post(f"{API_URL}/optimize-route", json=payload)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f"Route optimized! Total Distance: **{data['total_distance_km']} km**")
                        st.session_state["route_data"] = data
                        
                        # Show route path summary
                        route = data["routes"][0]["stops"]
                        path_str = " → ".join([s["label"] for s in route])
                        st.code(path_str, language="text")
                    else:
                        st.error(f"Error ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Parsing error: Ensure coordinates are valid 'lat,lon' format. {e}")

    with col_map:
        if "route_data" in st.session_state:
            # Draw map
            d_lat, d_lon = map(float, depot_input.split(","))
            m = folium.Map(location=[d_lat, d_lon], zoom_start=13, tiles="CartoDB dark_matter")
            
            route_stops = st.session_state["route_data"]["routes"][0]["stops"]
            
            # Draw markers
            for i, stop in enumerate(route_stops):
                is_depot = i == 0 or i == len(route_stops) - 1
                color = "red" if is_depot else "blue"
                icon = "home" if is_depot else "info-sign"
                folium.Marker(
                    [stop["lat"], stop["lon"]], 
                    popup=stop["label"], 
                    icon=folium.Icon(color=color, icon=icon)
                ).add_to(m)
            
            # Draw PolyLine
            points = [[s["lat"], s["lon"]] for s in route_stops]
            folium.PolyLine(points, color="cyan", weight=4, opacity=0.8).add_to(m)
            
            st_folium(m, width=700, height=500)
        else:
            st.info("Click 'Optimize Route' to generate the map.")


with tab3:
    st.header("Delivery Time Predictor")
    st.markdown("Using the **XGBoost Regressor** trained on 500k historical records.")
    
    c1, c2 = st.columns(2)
    with c1:
        dist = st.number_input("Trip Distance (miles)", min_value=0.1, value=2.5)
        hav_km = dist * 1.6  # approximation for UI speed
        hour = st.slider("Hour of Day (0-23)", 0, 23, 14)
        traffic = st.selectbox("Traffic Level", ["Light (25 mph)", "Moderate (15 mph)", "Heavy (8 mph)"], index=1)
    with c2:
        day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        day_idx = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day)
        is_weekend = 1 if day_idx >= 5 else 0
        
        speed_map = {"Light (25 mph)": 25.0, "Moderate (15 mph)": 15.0, "Heavy (8 mph)": 8.0}
        speed = speed_map[traffic]
        
    if st.button("Predict Duration", type="primary"):
        payload = {
            "trip_distance": dist,
            "haversine_km": hav_km,
            "hour_of_day": hour,
            "day_of_week": day_idx,
            "is_weekend": is_weekend,
            "speed_mph": speed
        }
        
        try:
            with st.spinner("Running ML Model..."):
                res = requests.post(f"{API_URL}/predict", json=payload)
                if res.status_code == 200:
                    mins = res.json()["predicted_duration_mins"]
                    st.success(f"### ⏱️ Estimated Delivery Time: **{mins} minutes**")
                else:
                    st.error(f"API Error ({res.status_code}): {res.text}")
        except Exception as e:
            st.error(f"Could not connect to API backend. Is it running? {e}")
