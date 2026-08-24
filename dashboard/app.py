import json
import math
import os
import random
from pathlib import Path

import folium
import joblib
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).parent.parent
ICON_DIR = ROOT / "Assets" / "PIYU_APP_ICONS_PNG"
MODEL_PATH = ROOT / "model" / "best_model.pkl"
METRICS_PATH = ROOT / "model" / "metrics.json"
API_URL = os.getenv("API_URL", "").rstrip("/")
if not API_URL:
    try:
        API_URL = st.secrets.get("API_URL", "").rstrip("/")
    except Exception:
        API_URL = ""
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

st.set_page_config(
    page_title="Last Mile | Fleet Intelligence",
    page_icon=str(ICON_DIR / "PIYU-AppIcon-180x180.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background:#070707; color:#f5f5f5; }
[data-testid="stSidebar"] { background:#0b0b0b; border-right:1px solid #292929; }
[data-testid="stHeader"] { background:#070707; }
.stMarkdown,.stText,label,p,h1,h2,h3,h4,h5 { color:#f5f5f5 !important; }
[data-testid="stMetric"] { background:#101010; border:1px solid #292929; border-radius:12px; padding:14px; }
[data-testid="stMetricValue"] { color:#ff3030 !important; }
.stButton>button,.stDownloadButton>button { background:#111; color:#fff; border:1px solid #d91f26; border-radius:8px; }
.stButton>button:hover,.stDownloadButton>button:hover { background:#d91f26; color:#fff; }
button[kind="primary"] { background:#e3262e !important; color:#fff !important; border-color:#ff4a4a !important; }
button[kind="primary"]:hover { background:#b9151d !important; }
[data-baseweb="tab"] { color:#ddd; }
[aria-selected="true"] { color:#ff3030 !important; }
[data-baseweb="tab-highlight"] { background:#e3262e !important; }
[data-baseweb="select"]>div,textarea,input { background:#111 !important; color:#fff !important; border-color:#333 !important; }
[data-testid="stDataFrame"] { border:1px solid #292929; }
.status-card { padding:12px 14px; border:1px solid #292929; border-radius:10px; background:#101010; margin-bottom:10px; }
.hero { border:1px solid #292929; border-radius:16px; padding:22px; background:linear-gradient(135deg,#0d0d0d,#16090a); margin-bottom:18px; }
.hero-accent { color:#ff3030; font-weight:700; letter-spacing:2px; font-size:12px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def get_osrm_routes(routes_coords):
    output = []
    for coords in routes_coords:
        try:
            coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
            r = requests.get(
                f"{OSRM_URL}/{coord_str}",
                params={"overview":"full","geometries":"geojson"},
                headers={"User-Agent":"LastMileOptimization/2.0"},
                timeout=8,
            )
            r.raise_for_status()
            routes = r.json().get("routes", [])
            if routes:
                output.append([[lat, lon] for lon, lat in routes[0]["geometry"]["coordinates"]])
                continue
        except requests.RequestException:
            pass
        output.append(list(coords))
    return output

@st.cache_resource(show_spinner=False)
def load_local_model():
    if not MODEL_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def load_metrics():
    if METRICS_PATH.exists():
        try:
            return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

@st.cache_data(ttl=10, show_spinner=False)
def remote_health():
    if not API_URL:
        return False, {}
    try:
        r = requests.get(f"{API_URL}/health", timeout=4)
        return r.ok, r.json()
    except requests.RequestException:
        return False, {}

def local_health():
    return True, {"status":"ok","eta_model_loaded":load_local_model() is not None}

def parse_stops(text):
    stops, demands = [], [0]
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            raise ValueError(f"Stop line {line_no}: use Lat, Lon, Demand")
        lat, lon = float(parts[0]), float(parts[1])
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Stop line {line_no}: invalid coordinates")
        demand = int(parts[2]) if len(parts) >= 3 else 1
        if demand < 0:
            raise ValueError(f"Stop line {line_no}: demand cannot be negative")
        stops.append({"lat":lat,"lon":lon})
        demands.append(demand)
    if not stops:
        raise ValueError("Add at least one delivery stop.")
    return stops, demands

def route_rows(data):
    return [{
        "Vehicle": r["vehicle_id"] + 1,
        "Stops": max(0, len(r["stops"]) - 2),
        "Distance (km)": r["distance_km"],
        "Load": r["load"],
    } for r in data.get("routes", [])]

def local_optimize(depot, stops, vehicles, capacity, demands, traffic):
    from model.route_optimizer import solve_vrp
    return solve_vrp(
        depot_coords=depot,
        stops_coords=[(s["lat"], s["lon"]) for s in stops],
        num_vehicles=vehicles,
        vehicle_capacities=[capacity] * vehicles,
        demands=demands,
        traffic_factor=traffic,
    )

def optimize(payload):
    if API_URL:
        try:
            r = requests.post(f"{API_URL}/optimize-route", json=payload, timeout=25)
            r.raise_for_status()
            return r.json(), "FastAPI"
        except requests.RequestException:
            pass
    result = local_optimize(
        (payload["depot"]["lat"], payload["depot"]["lon"]),
        payload["stops"], payload["num_vehicles"],
        payload["vehicle_capacities"][0], payload["demands"], payload["traffic_factor"],
    )
    return result, "Local engine"

def predict_eta(distance, haversine_km, hour, day, speed):
    model = load_local_model()
    if API_URL:
        try:
            payload = {
                "trip_distance":distance,"haversine_km":haversine_km,
                "hour_of_day":hour,"day_of_week":day,"is_weekend":int(day >= 5),"speed_mph":speed,
            }
            r = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
            r.raise_for_status()
            return r.json(), "FastAPI"
        except requests.RequestException:
            pass
    if model is not None:
        prediction = model.predict(pd.DataFrame([{
            "haversine_km":haversine_km,"hour_of_day":hour,
            "day_of_week":day,"is_weekend":int(day >= 5),"speed_mph":speed,
        }]))[0]
        return {"predicted_duration_mins":round(float(prediction),2),"model_used":"trained_model"}, "Local ML"
    base = distance / speed * 60
    traffic = 1 + 0.5 * math.sin(hour / 24 * math.pi)
    return {"predicted_duration_mins":round(base * traffic,2),"model_used":"analytical_fallback"}, "Local fallback"

local_ok, local_health_data = local_health()
remote_ok, remote_health_data = remote_health()
backend_online = local_ok or remote_ok
backend_mode = "FastAPI" if remote_ok else "Local engine"

st.markdown('<div class="hero"><div class="hero-accent">FLEET INTELLIGENCE PLATFORM</div><h1>Last-Mile Delivery Optimization</h1><p>Optimize routes. Predict ETA. Compare scenarios. Control delivery cost.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    logo = ICON_DIR / "PIYU-icon-white_512x512.png"
    if logo.exists():
        st.image(str(logo), width=76)
    st.markdown("## LAST MILE")
    st.caption("LOGISTICS OPTIMIZATION SYSTEM")
    st.divider()
    st.subheader("SYSTEM STATUS")
    if remote_ok:
        st.success("● API ONLINE")
        st.caption("Primary: FastAPI")
    else:
        st.success("● LOCAL ENGINE ONLINE")
        st.caption("No API_URL required — Streamlit runs the optimizer locally.")
    if st.button("↻ Refresh status", use_container_width=True):
        remote_health.clear()
        st.rerun()
    if remote_ok and remote_health_data.get("eta_model_loaded"):
        st.caption("ETA model: XGBoost/production model")
    elif load_local_model() is not None:
        st.caption("ETA model: local trained model")

metrics = load_metrics()
best = metrics.get("best_model", "XGBoost")
hero_cols = st.columns(4)
hero_cols[0].metric("ETA MODEL", best)
hero_cols[1].metric("ETA R²", metrics.get("results", {}).get(best, {}).get("R2", "0.888"))
hero_cols[2].metric("ROUTING", "OR-Tools")
hero_cols[3].metric("ENGINE", backend_mode)

route_tab, analytics_tab, eta_tab, scenario_tab, reports_tab = st.tabs([
    "ROUTE CONTROL", "FLEET ANALYTICS", "ETA INTELLIGENCE", "SCENARIO LAB", "REPORTS"
])

with route_tab:
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.subheader("Route Control")
        preset = st.selectbox("Operating preset", ["Custom", "Small Fleet", "Busy Day", "High Traffic"])
        presets = {
            "Small Fleet":(2,20,1.0), "Busy Day":(4,25,1.3), "High Traffic":(5,30,1.8), "Custom":(2,20,1.0)
        }
        pv = presets[preset]
        vehicles = st.number_input("Vehicles", 1, 20, pv[0])
        capacity = st.number_input("Capacity / vehicle", 1, 200, pv[1])
        traffic_name = st.selectbox("Traffic", ["Clear","Moderate","Heavy"], index={1.0:0,1.3:1,1.8:2}[pv[2]])
        traffic = {"Clear":1.0,"Moderate":1.3,"Heavy":1.8}[traffic_name]
        depot_text = st.text_input("Depot — Lat, Lon", "40.750,-73.990")
        default_stops = "40.748,-73.985,5\n40.761,-73.978,7\n40.732,-73.996,4\n40.739,-73.988,6\n40.755,-73.973,8\n40.765,-73.982,3"
        if "dyn_stops" not in st.session_state:
            st.session_state.dyn_stops = default_stops
        st.text_area("Orders — Lat, Lon, Demand", key="dyn_stops", height=190)
        a,b = st.columns(2)
        with a:
            if st.button("+ Live order", use_container_width=True):
                st.session_state.dyn_stops += f"\n{random.uniform(40.73,40.77):.4f},{random.uniform(-74,-73.97):.4f},{random.randint(1,5)}"
                st.rerun()
        with b:
            clear = st.button("Clear orders", use_container_width=True)
            if clear:
                st.session_state.dyn_stops = ""
                st.rerun()
        if st.button("OPTIMIZE FLEET", type="primary", use_container_width=True):
            try:
                dlat, dlon = [float(x.strip()) for x in depot_text.split(",")]
                stops, demands = parse_stops(st.session_state.dyn_stops)
                if sum(demands) > vehicles * capacity:
                    raise ValueError("Total demand exceeds fleet capacity. Increase vehicles/capacity or reduce demand.")
                payload = {
                    "depot":{"lat":dlat,"lon":dlon},"stops":stops,
                    "num_vehicles":vehicles,"vehicle_capacities":[capacity]*vehicles,
                    "demands":demands,"traffic_factor":traffic,
                }
                with st.spinner("Solving capacitated vehicle routing..."):
                    result, engine = optimize(payload)
                st.session_state.route_data = result
                st.session_state.route_engine = engine
                st.session_state.depot_coords = [dlat,dlon]
                st.session_state.optimization_config = {"vehicles":vehicles,"capacity":capacity,"traffic":traffic_name,"orders":len(stops)}
                st.success(f"Feasible route found • {engine}")
            except (ValueError, TypeError) as exc:
                st.error(str(exc))
    with right:
        data = st.session_state.get("route_data")
        if data and data.get("routes"):
            st.subheader("Live Fleet Map")
            loc = st.session_state["depot_coords"]
            m = folium.Map(location=loc, zoom_start=13, tiles="CartoDB dark_matter")
            folium.Marker(loc, popup="DEPOT", icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
            coords = [[[s["lat"],s["lon"]] for s in r["stops"]] for r in data["routes"]]
            road = get_osrm_routes(tuple(tuple(tuple(p) for p in r) for r in coords))
            for i,r in enumerate(data["routes"]):
                folium.PolyLine(road[i], color="#e3262e", weight=5, opacity=.9, tooltip=f"Vehicle {i+1}").add_to(m)
                for stop in r["stops"]:
                    if stop["node"]:
                        folium.Marker([stop["lat"],stop["lon"]], popup=stop["label"], icon=folium.Icon(color="red",icon="shopping-cart",prefix="fa")).add_to(m)
            st_folium(m, width=900, height=590)
        else:
            st.info("Set your fleet and orders, then run optimization.")

with analytics_tab:
    data = st.session_state.get("route_data")
    st.subheader("Fleet Command Center")
    if data and data.get("routes"):
        cfg = st.session_state.get("optimization_config", {})
        total = data["total_distance_km"]
        baseline = data["baseline_distance_km"]
        saved = data["saved_distance_km"]
        improvement = data["efficiency_improvement_pct"]
        load = sum(r["load"] for r in data["routes"])
        max_load = cfg.get("capacity",1) * len(data["routes"])
        utilization = round(load/max_load*100,1) if max_load else 0
        fuel_l = total * 0.11
        fuel_cost = fuel_l * 105
        co2 = fuel_l * 2.31
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("OPTIMIZED",f"{total:.2f} km")
        c2.metric("SAVED",f"{saved:.2f} km")
        c3.metric("EFFICIENCY",f"{improvement:.1f}%")
        c4.metric("UTILIZATION",f"{utilization}%")
        c5.metric("FUEL",f"{fuel_l:.1f} L")
        c6.metric("CO₂",f"{co2:.1f} kg")
        df = pd.DataFrame(route_rows(data))
        st.dataframe(df,use_container_width=True,hide_index=True)
        x,y,z = st.columns(3)
        with x: st.bar_chart(df.set_index("Vehicle")["Distance (km)"])
        with y: st.bar_chart(df.set_index("Vehicle")["Load"])
        with z: st.bar_chart(pd.DataFrame({"km":[baseline,total]},index=["Baseline","Optimized"]))
        st.info(f"Estimated fuel cost: ₹{fuel_cost:,.0f} • CO₂ model uses a documented scenario assumption of 0.11 L/km and 2.31 kg CO₂/L.")
    else:
        st.info("Run an optimization to unlock fleet analytics.")

with eta_tab:
    st.subheader("ETA Intelligence")
    left,right = st.columns(2)
    with left:
        distance = st.number_input("Trip distance (miles)",.1,100.,2.5)
        hour = st.slider("Hour",0,23,14)
        speed_label = st.selectbox("Average speed",["Light — 25 mph","Moderate — 15 mph","Heavy — 8 mph"],index=1)
    with right:
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        day_name = st.selectbox("Day",days)
        speed = {"Light — 25 mph":25.,"Moderate — 15 mph":15.,"Heavy — 8 mph":8.}[speed_label]
        st.metric("Validation RMSE",f"{metrics.get('results',{}).get(best,{}).get('RMSE_mins',2.98)} min")
    if st.button("PREDICT ETA",type="primary",use_container_width=True):
        result,engine = predict_eta(distance,distance*1.6,hour,days.index(day_name),speed)
        st.success(f"Predicted delivery time: {result['predicted_duration_mins']} minutes")
        st.caption(f"Engine: {engine} • Model: {result.get('model_used','unknown')}")

with scenario_tab:
    st.subheader("Scenario Lab")
    st.caption("Run operational what-if scenarios against the same order set.")
    scenarios = {
        "Normal":(2,20,1.0),"Peak traffic":(4,25,1.8),"High demand":(5,30,1.3),"Resilient fleet":(6,25,1.3)
    }
    chosen = st.selectbox("Scenario",list(scenarios))
    sv,sc,stf = scenarios[chosen]
    st.write(f"**{chosen}:** {sv} vehicles • {sc} capacity • {stf}× traffic")
    if st.button("RUN WHAT-IF",type="primary"):
        try:
            dlat,dlon=[float(x.strip()) for x in st.session_state.get("depot_coords",[40.75,-73.99])]
            stops,demands=parse_stops(st.session_state.get("dyn_stops",default_stops))
            if sum(demands)>sv*sc:
                st.error("Scenario is infeasible: fleet capacity is below demand.")
            else:
                result=local_optimize((dlat,dlon),stops,sv,sc,demands,stf)
                st.session_state.scenario_result=result
                st.success(f"Scenario distance: {result['total_distance_km']:.2f} km")
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.get("scenario_result"):
        sr=st.session_state["scenario_result"]
        st.dataframe(pd.DataFrame([{"Scenario":chosen,"Distance (km)":sr["total_distance_km"],"Saved (km)":sr["saved_distance_km"],"Improvement %":sr["efficiency_improvement_pct"]}]),use_container_width=True,hide_index=True)

with reports_tab:
    st.subheader("Reports & Audit Trail")
    data = st.session_state.get("route_data")
    if data and data.get("routes"):
        cfg=st.session_state.get("optimization_config",{})
        summary={
            "engine":st.session_state.get("route_engine","Local engine"),
            "optimized_distance_km":data["total_distance_km"],
            "baseline_distance_km":data["baseline_distance_km"],
            "saved_distance_km":data["saved_distance_km"],
            "efficiency_improvement_pct":data["efficiency_improvement_pct"],
            "vehicles":len(data["routes"]),"orders":cfg.get("orders",0),
            "traffic":cfg.get("traffic","Unknown"),"vehicle_capacity":cfg.get("capacity",0),
        }
        st.json(summary)
        routes_df=pd.DataFrame(route_rows(data))
        st.download_button("DOWNLOAD FLEET CSV",routes_df.to_csv(index=False).encode(),"fleet_route_report.csv","text/csv",use_container_width=True)
        st.download_button("DOWNLOAD JSON AUDIT",json.dumps({"summary":summary,"routes":data["routes"]},indent=2).encode(),"optimization_audit.json","application/json",use_container_width=True)
    else:
        st.info("Run an optimization to generate an auditable report.")

st.divider()
st.caption("Last-Mile Delivery Optimization • OR-Tools CVRP • ML ETA • OSRM • Streamlit • FastAPI")
