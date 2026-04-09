import sys
import json
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path
import pandas as pd
import random

ROOT = Path(__file__).parent.parent
STATS_PATH = ROOT / "data" / "dataset_stats.json"
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Last Mile Delivery Optimizer", page_icon="🚚", layout="wide", initial_sidebar_state="expanded")

st.title("🚚 Last Mile Delivery Optimization")
st.markdown("Production-ready VRPTW routing system with multiple vehicles, capacity constraints, and traffic dynamics.")

@st.cache_data
def load_stats():
    if STATS_PATH.exists():
        with open(STATS_PATH, "r") as f: return json.load(f)
    return {}
stats = load_stats()

tab1, tab2, tab3 = st.tabs(["🗺️ Route Optimizer (VRP)", "📊 Evaluation Metrics", "🤖 Time Predictor"])

with tab1:
    col_input, col_map = st.columns([1, 2])
    with col_input:
        st.subheader("Vehicle Configuration")
        num_vehicles = st.number_input("Number of Vehicles", min_value=1, max_value=10, value=2)
        vehicle_cap = st.number_input("Vehicle Capacity (units)", min_value=5, max_value=100, value=20)
        traffic_condition = st.selectbox("Traffic Condition Factor", ["Clear (1.0x delay)", "Moderate (1.3x delay)", "Heavy (1.8x delay)"])
        tf_dict = {"Clear (1.0x delay)": 1.0, "Moderate (1.3x delay)": 1.3, "Heavy (1.8x delay)": 1.8}
        
        st.subheader("Locations & Demand")
        depot_input = st.text_input("Depot (Lat, Lon)", "40.750,-73.990")
        default_stops = "40.748,-73.985,5\n40.761,-73.978,7\n40.732,-73.996,4\n40.739,-73.988,6\n40.755,-73.973,8\n40.765,-73.982,3"
        stops_input = st.text_area("Stops (Lat, Lon, Demand)", default_stops, height=180)
        
        if st.button("Optimize Fleet Route", type="primary"):
            d_lat, d_lon = map(float, depot_input.split(","))
            depot = {"lat": d_lat, "lon": d_lon}
            stops = []
            demands = [0] # index 0 is depot
            try:
                for line in stops_input.split("\n"):
                    if line.strip():
                        parts = line.split(",")
                        lat, lon = float(parts[0]), float(parts[1])
                        stops.append({"lat": lat, "lon": lon})
                        if len(parts) > 2: demands.append(int(parts[2]))
                        else: demands.append(1)
                
                payload = {
                    "depot": depot,
                    "stops": stops,
                    "num_vehicles": num_vehicles,
                    "vehicle_capacities": [vehicle_cap]*num_vehicles,
                    "demands": demands,
                    "traffic_factor": tf_dict[traffic_condition]
                }
                
                with st.spinner("Solving advanced VRP..."):
                    res = requests.post(f"{API_URL}/optimize-route", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["route_data"] = data
                        st.session_state["depot_coords"] = [d_lat, d_lon]
                        st.success(f"Optimal paths found!")
                    else: st.error(res.text)
            except Exception as e: st.error(f"Error parsing: {e}")

    with col_map:
        if "route_data" in st.session_state and 'routes' in st.session_state["route_data"]:
            st.subheader("Interactive Dispatched Map")
            data = st.session_state["route_data"]
            loc = st.session_state["depot_coords"]
            
            m = folium.Map(location=loc, zoom_start=13, tiles="CartoDB positron")
            colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue', 'pink']
            
            # Draw Depot
            folium.Marker(loc, popup="Global Depot", icon=folium.Icon(color='red', icon='home', prefix='fa')).add_to(m)
            
            for i, r in enumerate(data['routes']):
                c = colors[i % len(colors)]
                pts = [[s["lat"], s["lon"]] for s in r['stops']]
                folium.PolyLine(pts, color=c, weight=5, opacity=0.8, tooltip=f"Vehicle {r['vehicle_id']}").add_to(m)
                
                # Markers
                for idx, stop in enumerate(r['stops']):
                    if "Return" not in stop['label'] and stop['node'] != 0:
                        folium.Marker(
                            [stop["lat"], stop["lon"]], 
                            popup=stop["label"], 
                            icon=folium.Icon(color=c, icon='shopping-cart')
                        ).add_to(m)
            st_folium(m, width=800, height=600)

with tab2:
    st.header("Logistics Performance Metrics")
    data = st.session_state.get("route_data", None)
    if data and "routes" in data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Unoptimized Baseline", f"{data['baseline_distance_km']} km")
        c2.metric("Optimized Distance VRP", f"{data['total_distance_km']} km", delta=f"-{data['saved_distance_km']} km")
        c3.metric("Efficiency Improvement", f"{data['efficiency_improvement_pct']} %", delta="Optimized")
        
        st.markdown("### Vehicle Metrics")
        df_list = []
        for r in data['routes']:
            df_list.append({"Vehicle ID": r['vehicle_id'], "Stops Visited": len(r['stops']) - 2, "Distance (km)": r['distance_km'], "Cargo Load Used": r['load']})
        st.dataframe(pd.DataFrame(df_list), use_container_width=True)
    else: st.info("Run optimization on the first tab to view metrics.")

with tab3:
    st.header("Delivery Time Predictor")
    st.markdown("Simulated duration via dynamic distance and traffic patterns.")
    c1, c2 = st.columns(2)
    with c1:
        dist = st.number_input("Trip Distance (miles)", min_value=0.1, value=2.5)
        hav_km = dist * 1.6
        hour = st.slider("Hour of Day (0-23)", 0, 23, 14)
        traffic = st.selectbox("Traffic Speed", ["Light (25 mph)", "Moderate (15 mph)", "Heavy (8 mph)"], index=1)
    with c2:
        day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        speed_map = {"Light (25 mph)": 25.0, "Moderate (15 mph)": 15.0, "Heavy (8 mph)": 8.0}
        speed = speed_map[traffic]
    if st.button("Predict Duration", type="primary"):
        payload = {"trip_distance": dist, "haversine_km": hav_km, "hour_of_day": hour, "day_of_week": 1, "is_weekend": 0, "speed_mph": speed}
        try:
            with st.spinner("Model executing..."):
                res = requests.post(f"{API_URL}/predict", json=payload)
                if res.status_code == 200: st.success(f"### ⏱️ ETA: **{res.json()['predicted_duration_mins']} mins**")
                else: st.error("Error connecting to predictor engine.")
        except Exception as e: st.error(f"Failed to connect: {e}")
