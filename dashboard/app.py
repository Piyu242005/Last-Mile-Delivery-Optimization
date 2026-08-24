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
ICON_DIR = ROOT / "Assets" / "PIYU_APP_ICONS_PNG"
API_URL = os.getenv("API_URL", "").rstrip("/")
if not API_URL:
    try:
        API_URL = st.secrets.get("API_URL", "").rstrip("/")
    except Exception:
        API_URL = ""
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

st.set_page_config(page_title="Last Mile Delivery Optimization", page_icon=str(ICON_DIR / "PIYU-AppIcon-180x180.png"), layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #080808; color: #f5f5f5; }
[data-testid="stSidebar"] { background: #0d0d0d; border-right: 1px solid #2a2a2a; }
[data-testid="stHeader"] { background: #080808; }
.stMarkdown, .stText, label, p, h1, h2, h3, h4 { color: #f5f5f5 !important; }
div[data-testid="stMetric"] { background: #101010; border: 1px solid #2b2b2b; border-radius: 12px; padding: 14px; }
div[data-testid="stMetricValue"] { color: #ff2b2b !important; }
.stButton > button, .stDownloadButton > button { background: #111111; color: #ffffff; border: 1px solid #e32626; border-radius: 8px; }
.stButton > button:hover, .stDownloadButton > button:hover { background: #e32626; color: #ffffff; border-color: #ff4444; }
button[kind="primary"] { background: #e32626 !important; color: #ffffff !important; border-color: #ff4444 !important; }
button[kind="primary"]:hover { background: #b51212 !important; }
[data-baseweb="tab"] { color: #dddddd; }
[aria-selected="true"] { color: #ff3030 !important; }
[data-baseweb="tab-highlight"] { background: #e32626 !important; }
[data-baseweb="select"] > div, textarea, input { background: #111111 !important; color: #ffffff !important; border-color: #333333 !important; }
[data-testid="stDataFrame"] { border: 1px solid #2a2a2a; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def get_osrm_routes(routes_coords):
    results = []
    for coords in routes_coords:
        try:
            coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
            response = requests.get(f"{OSRM_URL}/{coord_str}", params={"overview": "full", "geometries": "geojson"}, headers={"User-Agent": "LastMileOptimization/1.0"}, timeout=8)
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

def route_rows(route_data):
    return [{"Vehicle": route["vehicle_id"] + 1, "Stops": max(0, len(route["stops"]) - 2), "Distance (km)": route["distance_km"], "Load": route["load"]} for route in route_data.get("routes", [])]

load_stats()
st.image(str(ICON_DIR / "PIYU-icon-black_512x512.png"), width=80)
st.title("Last Mile Delivery Optimization")
st.caption("ML-powered ETA • Fleet Routing • Geospatial Analytics")

st.sidebar.image(str(ICON_DIR / "PIYU-icon-white_512x512.png"), width=80)
st.sidebar.markdown("# **LAST MILE**")
st.sidebar.caption("LOGISTICS OPTIMIZATION SYSTEM")
st.sidebar.divider()
st.sidebar.subheader("SYSTEM STATUS")
if not API_URL:
    st.sidebar.error("API_URL not configured")
    st.sidebar.caption("Set API_URL in Streamlit Cloud → Settings → Secrets.")
else:
    st.sidebar.caption(f"API: {API_URL}")
if st.sidebar.button("↻ Refresh API Status", use_container_width=True):
    check_api.clear()
    st.rerun()
api_ok, api_health = check_api()
if api_ok:
    st.sidebar.success("● BACKEND ONLINE")
    st.sidebar.info(f"ETA model: {'TRAINED' if api_health.get('eta_model_loaded') else 'FALLBACK'}")
else:
    st.warning("Backend API is unavailable. Configure API_URL and deploy the FastAPI service.")

# Black/red portfolio navigation.
tab1, tab2, tab3, tab4, tab5 = st.tabs(["ROUTE OPTIMIZER", "FLEET ANALYTICS", "ETA PREDICTOR", "SCENARIOS", "REPORTS"])

with tab1:
    col_input, col_map = st.columns([1, 2])
    with col_input:
        st.subheader("Fleet Configuration")
        preset = st.selectbox("Scenario Preset", ["Custom", "Small Fleet", "Busy Day", "High Traffic"])
        preset_values = {"Small Fleet": (2, 20, "Clear (1.0x delay)"), "Busy Day": (4, 25, "Moderate (1.3x delay)"), "High Traffic": (5, 30, "Heavy (1.8x delay)")}
        default_vehicles, default_capacity, default_traffic = preset_values.get(preset, (2, 20, "Clear (1.0x delay)"))
        num_vehicles = st.number_input("Number of Vehicles", min_value=1, max_value=10, value=default_vehicles)
        vehicle_cap = st.number_input("Vehicle Capacity", min_value=5, max_value=100, value=default_capacity)
        traffic_condition = st.selectbox("Traffic Condition", ["Clear (1.0x delay)", "Moderate (1.3x delay)", "Heavy (1.8x delay)"], index=["Clear (1.0x delay)", "Moderate (1.3x delay)", "Heavy (1.8x delay)"].index(default_traffic))
        tf_dict = {"Clear (1.0x delay)": 1.0, "Moderate (1.3x delay)": 1.3, "Heavy (1.8x delay)": 1.8}
        st.subheader("Locations & Demand")
        depot_input = st.text_input("Depot (Lat, Lon)", "40.750,-73.990")
        default_stops = "40.748,-73.985,5\n40.761,-73.978,7\n40.732,-73.996,4\n40.739,-73.988,6\n40.755,-73.973,8\n40.765,-73.982,3"
        if "dyn_stops" not in st.session_state:
            st.session_state.dyn_stops = default_stops
        st.text_area("Stops (Lat, Lon, Demand)", height=180, key="dyn_stops")
        if st.button("+ Add Live Order", use_container_width=True):
            st.session_state.dyn_stops += f"\n{random.uniform(40.730, 40.770):.4f},{random.uniform(-74.000, -73.970):.4f},{random.randint(1,5)}"
            st.rerun()
        if st.button("OPTIMIZE FLEET ROUTE", type="primary", disabled=not api_ok, use_container_width=True):
            try:
                d_lat, d_lon = map(float, depot_input.split(","))
                stops, demands = [], [0]
                for line in st.session_state.dyn_stops.splitlines():
                    if line.strip():
                        parts = [part.strip() for part in line.split(",")]
                        if len(parts) < 2: raise ValueError("Each stop needs latitude and longitude.")
                        stops.append({"lat": float(parts[0]), "lon": float(parts[1])})
                        demands.append(int(parts[2]) if len(parts) > 2 else 1)
                if sum(demands) > num_vehicles * vehicle_cap: raise ValueError("Total demand exceeds fleet capacity.")
                payload = {"depot": {"lat": d_lat, "lon": d_lon}, "stops": stops, "num_vehicles": num_vehicles, "vehicle_capacities": [vehicle_cap] * num_vehicles, "demands": demands, "traffic_factor": tf_dict[traffic_condition]}
                with st.spinner("Optimizing fleet with OR-Tools..."):
                    response = requests.post(f"{API_URL}/optimize-route", json=payload, timeout=25)
                response.raise_for_status()
                st.session_state.route_data = response.json()
                st.session_state.depot_coords = [d_lat, d_lon]
                st.session_state.optimization_config = {"vehicles": num_vehicles, "capacity": vehicle_cap, "traffic": traffic_condition, "orders": len(stops)}
                st.success("Route optimized successfully.")
            except (ValueError, requests.RequestException) as exc:
                st.error(f"Optimization failed: {exc}")
    with col_map:
        data = st.session_state.get("route_data")
        if data and data.get("routes"):
            st.subheader("Live Route Map")
            loc = st.session_state["depot_coords"]
            m = folium.Map(location=loc, zoom_start=13, tiles="CartoDB dark_matter")
            folium.Marker(loc, popup="Depot", icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
            all_pts = [[[s["lat"], s["lon"]] for s in route["stops"]] for route in data["routes"]]
            osrm_routes = get_osrm_routes(tuple(tuple(tuple(p) for p in route) for route in all_pts))
            for i, route in enumerate(data["routes"]):
                folium.PolyLine(osrm_routes[i], color="#e32626", weight=5, opacity=0.9, tooltip=f"Vehicle {route['vehicle_id'] + 1}").add_to(m)
                for stop in route["stops"]:
                    if stop["node"] != 0:
                        folium.Marker([stop["lat"], stop["lon"]], popup=stop["label"], icon=folium.Icon(color="red", icon="shopping-cart", prefix="fa")).add_to(m)
            st_folium(m, width=800, height=600)
        else:
            st.info("Configure your fleet and optimize a route.")

with tab2:
    st.header("Fleet Analytics")
    data = st.session_state.get("route_data")
    if data and data.get("routes"):
        total, baseline = data["total_distance_km"], data["baseline_distance_km"]
        saved, improvement = data["saved_distance_km"], data["efficiency_improvement_pct"]
        total_load = sum(r["load"] for r in data["routes"])
        capacity = st.session_state.get("optimization_config", {}).get("capacity", 20) * len(data["routes"])
        utilization = round(total_load / capacity * 100, 1) if capacity else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("OPTIMIZED", f"{total:.2f} km")
        c2.metric("SAVED", f"{saved:.2f} km")
        c3.metric("EFFICIENCY", f"{improvement:.2f}%")
        c4.metric("UTILIZATION", f"{utilization}%")
        df = pd.DataFrame(route_rows(data))
        st.dataframe(df, use_container_width=True, hide_index=True)
        a,b = st.columns(2)
        with a: st.bar_chart(df.set_index("Vehicle")["Distance (km)"])
        with b: st.bar_chart(df.set_index("Vehicle")["Load"])
        st.bar_chart(pd.DataFrame({"Distance (km)": [baseline, total]}, index=["Nearest Neighbor", "OR-Tools"]))
    else:
        st.info("Run an optimization first.")

with tab3:
    st.header("ETA Predictor")
    c1,c2 = st.columns(2)
    with c1:
        dist = st.number_input("Trip Distance (miles)", min_value=0.1, value=2.5)
        hav_km, hour = dist * 1.6, st.slider("Hour of Day", 0, 23, 14)
        traffic = st.selectbox("Traffic Speed", ["Light (25 mph)", "Moderate (15 mph)", "Heavy (8 mph)"], index=1)
    with c2:
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        day = st.selectbox("Day of Week", days)
        speed = {"Light (25 mph)":25.0,"Moderate (15 mph)":15.0,"Heavy (8 mph)":8.0}[traffic]
    if st.button("PREDICT DELIVERY TIME", type="primary", disabled=not api_ok, use_container_width=True):
        payload = {"trip_distance":dist,"haversine_km":hav_km,"hour_of_day":hour,"day_of_week":days.index(day),"is_weekend":int(days.index(day)>=5),"speed_mph":speed}
        try:
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            st.success(f"ETA: {result['predicted_duration_mins']} minutes")
            st.caption(f"Prediction engine: {result.get('model_used','unknown')}")
        except requests.RequestException as exc: st.error(f"Prediction failed: {exc}")

with tab4:
    st.header("Scenario Lab")
    st.markdown("### Compare operating conditions")
    scenarios = {"Normal": (2,20,1.0), "Peak Traffic": (4,25,1.8), "High Demand": (5,30,1.3)}
    scenario_df = pd.DataFrame([{"Scenario":k,"Vehicles":v[0],"Capacity":v[1],"Traffic Factor":v[2]} for k,v in scenarios.items()])
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
    st.info("Use the Route Optimizer presets to run each scenario and compare the resulting distance and fleet utilization.")

with tab5:
    st.header("Reports & Export")
    data = st.session_state.get("route_data")
    if data and data.get("routes"):
        config = st.session_state.get("optimization_config", {})
        summary = {"optimized_distance_km":data["total_distance_km"],"baseline_distance_km":data["baseline_distance_km"],"saved_distance_km":data["saved_distance_km"],"efficiency_improvement_pct":data["efficiency_improvement_pct"],"vehicles_used":len(data["routes"]),"orders":config.get("orders",0),"vehicle_capacity":config.get("capacity",0),"traffic_condition":config.get("traffic","Unknown")}
        st.json(summary)
        routes_df = pd.DataFrame(route_rows(data))
        st.download_button("DOWNLOAD FLEET CSV", routes_df.to_csv(index=False).encode("utf-8"), file_name="fleet_route_report.csv", mime="text/csv", use_container_width=True)
        st.download_button("DOWNLOAD OPTIMIZATION JSON", json.dumps({"summary":summary,"routes":data["routes"]},indent=2).encode("utf-8"), file_name="optimization_report.json", mime="application/json", use_container_width=True)
    else: st.info("Run an optimization to generate reports.")
