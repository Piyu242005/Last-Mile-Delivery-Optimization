import json
import os
import random
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

ROOT = Path(__file__).parent.parent
STATS_PATH = ROOT / "data" / "dataset_stats.json"
API_URL = os.getenv("API_URL", "").rstrip("/")
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

st.set_page_config(
    page_title="Last Mile Delivery Optimizer",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=3600, show_spinner=False)
def get_osrm_routes(routes_coords):
    results = []
    for coords in routes_coords:
        try:
            coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
            response = requests.get(
                f"{OSRM_URL}/{coord_str}",
                params={"overview": "full", "geometries": "geojson"},
                headers={"User-Agent": "LastMileOptimization/1.0"},
                timeout=8,
            )
            response.raise_for_status()
            routes = response.json().get("routes", [])
            if routes:
                results.append([[lat, lon] for lon, lat in routes[0]["geometry"]["coordinates"]])
                continue
        except requests.RequestException:
            pass
        results.append(list(coords))
    return results


@st.cache_data(show_spinner=False)
def load_stats():
    if STATS_PATH.exists():
        with open(STATS_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


@st.cache_data(ttl=10, show_spinner=False)
def check_api():
    if not API_URL:
        return False, {"error": "API_URL is not configured"}
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.ok, response.json()
    except requests.RequestException as exc:
        return False, {"error": str(exc)}


stats = load_stats()

st.title("🚚 Last Mile Delivery Optimization")
st.caption("ML-powered ETA prediction + capacitated vehicle routing")

st.sidebar.subheader("Backend Configuration")
if not API_URL:
    st.sidebar.error("API_URL is not configured")
    st.sidebar.caption("Set API_URL in Streamlit Cloud → Settings → Secrets.")
else:
    st.sidebar.caption(f"API: {API_URL}")

if st.sidebar.button("🔄 Refresh API Status"):
    check_api.clear()
    st.rerun()

api_ok, api_health = check_api()
if api_ok:
    st.sidebar.success("API connected")
else:
    st.warning("Backend API is unavailable. Configure API_URL and make sure the FastAPI service is deployed.")
    if api_health.get("error"):
        st.caption(f"Backend check: {api_health['error']}")


tab1, tab2, tab3 = st.tabs(["🗺️ Route Optimizer", "📊 Evaluation Metrics", "🤖 Time Predictor"])

with tab1:
    col_input, col_map = st.columns([1, 2])
    with col_input:
        st.subheader("Vehicle Configuration")
        num_vehicles = st.number_input("Number of Vehicles", min_value=1, max_value=10, value=2)
        vehicle_cap = st.number_input("Vehicle Capacity (units)", min_value=5, max_value=100, value=20)
        traffic_condition = st.selectbox("Traffic Condition", ["Clear (1.0x delay)", "Moderate (1.3x delay)", "Heavy (1.8x delay)"])
        tf_dict = {"Clear (1.0x delay)": 1.0, "Moderate (1.3x delay)": 1.3, "Heavy (1.8x delay)": 1.8}

        st.subheader("Locations & Demand")
        depot_input = st.text_input("Depot (Lat, Lon)", "40.750,-73.990")
        default_stops = "40.748,-73.985,5\n40.761,-73.978,7\n40.732,-73.996,4\n40.739,-73.988,6\n40.755,-73.973,8\n40.765,-73.982,3"
        if "dyn_stops" not in st.session_state:
            st.session_state.dyn_stops = default_stops
        st.text_area("Stops (Lat, Lon, Demand)", height=180, key="dyn_stops")

        if st.button("🌟 Add Live Order"):
            new_lat = round(random.uniform(40.730, 40.770), 4)
            new_lon = round(random.uniform(-74.000, -73.970), 4)
            new_demand = random.randint(1, 5)
            st.session_state.dyn_stops += f"\n{new_lat},{new_lon},{new_demand}"
            st.rerun()

        if st.button("Optimize Fleet Route", type="primary", disabled=not api_ok):
            try:
                d_lat, d_lon = map(float, depot_input.split(","))
                stops = []
                demands = [0]
                for line in st.session_state.dyn_stops.splitlines():
                    if line.strip():
                        parts = [part.strip() for part in line.split(",")]
                        if len(parts) < 2:
                            raise ValueError("Each stop needs latitude and longitude.")
                        stops.append({"lat": float(parts[0]), "lon": float(parts[1])})
                        demands.append(int(parts[2]) if len(parts) > 2 else 1)
                payload = {
                    "depot": {"lat": d_lat, "lon": d_lon},
                    "stops": stops,
                    "num_vehicles": num_vehicles,
                    "vehicle_capacities": [vehicle_cap] * num_vehicles,
                    "demands": demands,
                    "traffic_factor": tf_dict[traffic_condition],
                }
                with st.spinner("Optimizing fleet route..."):
                    response = requests.post(f"{API_URL}/optimize-route", json=payload, timeout=25)
                response.raise_for_status()
                st.session_state.route_data = response.json()
                st.session_state.depot_coords = [d_lat, d_lon]
                st.success("Route optimized successfully.")
            except (ValueError, requests.RequestException) as exc:
                st.error(f"Optimization failed: {exc}")

    with col_map:
        data = st.session_state.get("route_data")
        if data and data.get("routes"):
            st.subheader("Interactive Road Map")
            loc = st.session_state["depot_coords"]
            m = folium.Map(location=loc, zoom_start=13, tiles="CartoDB positron")
            colors = ["blue", "green", "purple", "orange", "darkred", "cadetblue", "pink"]
            folium.Marker(loc, popup="Depot", icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
            all_pts = [[[s["lat"], s["lon"]] for s in route["stops"]] for route in data["routes"]]
            osrm_routes = get_osrm_routes(tuple(tuple(tuple(p) for p in route) for route in all_pts))
            for i, route in enumerate(data["routes"]):
                color = colors[i % len(colors)]
                folium.PolyLine(osrm_routes[i], color=color, weight=5, opacity=0.8, tooltip=f"Vehicle {route['vehicle_id']}").add_to(m)
                for stop in route["stops"]:
                    if stop["node"] != 0:
                        folium.Marker([stop["lat"], stop["lon"]], popup=stop["label"], icon=folium.Icon(color=color, icon="shopping-cart", prefix="fa")).add_to(m)
            st_folium(m, width=800, height=600)
        else:
            st.info("Configure your fleet and click Optimize Fleet Route.")

with tab2:
    st.header("Logistics Performance Metrics")
    data = st.session_state.get("route_data")
    if data and data.get("routes"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline", f"{data['baseline_distance_km']} km")
        c2.metric("Optimized", f"{data['total_distance_km']} km", delta=f"-{data['saved_distance_km']} km")
        c3.metric("Improvement", f"{data['efficiency_improvement_pct']}%")
        rows = [{"Vehicle ID": route["vehicle_id"], "Stops Visited": len(route["stops"]) - 2, "Distance (km)": route["distance_km"], "Cargo Load": route["load"]} for route in data["routes"]]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("Run an optimization to view metrics.")

with tab3:
    st.header("Delivery Time Predictor")
    c1, c2 = st.columns(2)
    with c1:
        dist = st.number_input("Trip Distance (miles)", min_value=0.1, value=2.5)
        hav_km = dist * 1.6
        hour = st.slider("Hour of Day", 0, 23, 14)
        traffic = st.selectbox("Traffic Speed", ["Light (25 mph)", "Moderate (15 mph)", "Heavy (8 mph)"], index=1)
    with c2:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day = st.selectbox("Day of Week", days)
        speed_map = {"Light (25 mph)": 25.0, "Moderate (15 mph)": 15.0, "Heavy (8 mph)": 8.0}
        speed = speed_map[traffic]

    if st.button("Predict Duration", type="primary", disabled=not api_ok):
        payload = {"trip_distance": dist, "haversine_km": hav_km, "hour_of_day": hour, "day_of_week": days.index(day), "is_weekend": int(days.index(day) >= 5), "speed_mph": speed}
        try:
            with st.spinner("Predicting ETA..."):
                response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            st.success(f"### ⏱️ ETA: **{result['predicted_duration_mins']} mins**")
        except requests.RequestException as exc:
            st.error(f"Prediction failed: {exc}")
