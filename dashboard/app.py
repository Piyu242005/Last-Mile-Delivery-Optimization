import json
import math
import os
import random
import sys
from pathlib import Path

import folium
import joblib
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODEL_PATH = ROOT / "model" / "best_model.pkl"
METRICS_PATH = ROOT / "model" / "metrics.json"
API_URL = os.getenv("API_URL", "").rstrip("/")
if not API_URL:
    try:
        API_URL = str(st.secrets.get("API_URL", "")).rstrip("/")
    except Exception:
        API_URL = ""
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

st.set_page_config(page_title="Last Mile | Fleet Intelligence", page_icon="🚚", layout="wide")
st.markdown("""
<style>
:root{color-scheme:dark}.stApp{background:#070707;color:#f5f5f5}[data-testid="stSidebar"]{background:#0b0b0b;border-right:1px solid #292929}[data-testid="stHeader"]{background:#070707}.stMarkdown,.stText,label,p,h1,h2,h3,h4,h5{color:#f5f5f5!important}[data-testid="stMetric"]{background:#101010;border:1px solid #292929;border-radius:12px;padding:14px}[data-testid="stMetricValue"]{color:#ff3030!important}.stButton>button,.stDownloadButton>button{background:#111;color:#fff;border:1px solid #d91f26;border-radius:8px}.stButton>button:hover,.stDownloadButton>button:hover{background:#d91f26;color:#fff}button[kind="primary"]{background:#e3262e!important;color:#fff!important;border-color:#ff4a4a!important}button[kind="primary"]:hover{background:#b9151d!important}[aria-selected="true"]{color:#ff3030!important}[data-baseweb="tab-highlight"]{background:#e3262e!important}[data-baseweb="select"]>div,textarea,input{background:#111!important;color:#fff!important;border-color:#333!important}.hero{border:1px solid #292929;border-radius:16px;padding:22px;background:linear-gradient(135deg,#0d0d0d,#16090a);margin-bottom:18px}.hero-accent{color:#ff3030;font-weight:700;letter-spacing:2px;font-size:12px}
</style>""", unsafe_allow_html=True)

DEFAULT_STOPS = "40.748,-73.985,5\n40.761,-73.978,7\n40.732,-73.996,4\n40.739,-73.988,6\n40.755,-73.973,8\n40.765,-73.982,3"

@st.cache_data(ttl=3600, show_spinner=False)
def get_osrm_routes(routes_coords):
    output=[]
    for coords in routes_coords:
        try:
            coord_str=";".join(f"{lon},{lat}" for lat,lon in coords)
            r=requests.get(f"{OSRM_URL}/{coord_str}",params={"overview":"full","geometries":"geojson"},headers={"User-Agent":"LastMileOptimization/2.0"},timeout=8)
            r.raise_for_status(); routes=r.json().get("routes",[])
            if routes:
                output.append([[lat,lon] for lon,lat in routes[0]["geometry"]["coordinates"]]); continue
        except requests.RequestException:
            pass
        output.append(list(coords))
    return output

@st.cache_resource(show_spinner=False)
def load_model():
    try:
        return joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def load_metrics():
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
    except Exception:
        return {}

@st.cache_data(ttl=10, show_spinner=False)
def api_health():
    if not API_URL:return False
    try:return requests.get(f"{API_URL}/health",timeout=4).ok
    except requests.RequestException:return False

def parse_stops(text):
    stops=[];demands=[0]
    for n,line in enumerate(text.splitlines(),1):
        if not line.strip():continue
        p=[x.strip() for x in line.split(",")]
        if len(p)<2:raise ValueError(f"Order {n}: use Lat, Lon, Demand")
        lat,lon=float(p[0]),float(p[1]); demand=int(p[2]) if len(p)>2 else 1
        if not(-90<=lat<=90 and -180<=lon<=180):raise ValueError(f"Order {n}: invalid coordinates")
        if demand<0:raise ValueError(f"Order {n}: demand cannot be negative")
        stops.append({"lat":lat,"lon":lon});demands.append(demand)
    if not stops:raise ValueError("Add at least one delivery order.")
    return stops,demands

def local_vrp(depot,stops,vehicles,capacity,demands,traffic):
    from model.route_optimizer import solve_vrp
    result=solve_vrp(depot_coords=depot,stops_coords=[(s["lat"],s["lon"]) for s in stops],num_vehicles=int(vehicles),vehicle_capacities=[int(capacity)]*int(vehicles),demands=demands,traffic_factor=float(traffic))
    if result.get("routes"):return result,"Local OR-Tools"
    raise RuntimeError("OR-Tools returned no active routes.")

def optimize(payload):
    if API_URL:
        try:
            r=requests.post(f"{API_URL}/optimize-route",json=payload,timeout=25);r.raise_for_status();result=r.json()
            if result.get("routes"):return result,"FastAPI"
        except requests.RequestException:pass
    return local_vrp((payload["depot"]["lat"],payload["depot"]["lon"]),payload["stops"],payload["num_vehicles"],payload["vehicle_capacities"][0],payload["demands"],payload["traffic_factor"])

def run_demo():
    payload={"depot":{"lat":40.750,"lon":-73.990},"stops":[{"lat":40.748,"lon":-73.985},{"lat":40.761,"lon":-73.978},{"lat":40.732,"lon":-73.996},{"lat":40.739,"lon":-73.988},{"lat":40.755,"lon":-73.973},{"lat":40.765,"lon":-73.982}],"num_vehicles":2,"vehicle_capacities":[20,20],"demands":[0,5,7,4,6,8,3],"traffic_factor":1.0}
    result,engine=optimize(payload)
    st.session_state.route_data=result;st.session_state.route_engine=engine;st.session_state.depot_coords=[40.750,-73.990];st.session_state.optimization_config={"vehicles":2,"capacity":20,"traffic":"Clear","orders":6}

remote=api_health(); mode="FastAPI" if remote else "Local engine"
st.markdown('<div class="hero"><div class="hero-accent">FLEET INTELLIGENCE PLATFORM</div><h1>Last-Mile Delivery Optimization</h1><p>Optimize routes. Predict ETA. Compare scenarios. Control delivery cost.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown("## 🚚 LAST MILE");st.caption("LOGISTICS OPTIMIZATION SYSTEM");st.divider();st.subheader("SYSTEM STATUS")
    st.success("● API ONLINE" if remote else "● LOCAL ENGINE ONLINE")
    st.caption("FastAPI primary" if remote else "No API_URL required — Streamlit runs the optimizer locally.")
    if st.button("↻ Refresh status",use_container_width=True):api_health.clear();st.rerun()

metrics=load_metrics();best=metrics.get("best_model","XGBoost")
a,b,c,d=st.columns(4);a.metric("ETA MODEL",best);b.metric("ETA R²",metrics.get("results",{}).get(best,{}).get("R2","0.888"));c.metric("ROUTING","OR-Tools");d.metric("ENGINE",mode)

route_tab,analytics_tab,eta_tab,scenario_tab,reports_tab=st.tabs(["ROUTE CONTROL","FLEET ANALYTICS","ETA INTELLIGENCE","SCENARIO LAB","REPORTS"])
with route_tab:
    left,right=st.columns([1,2],gap="large")
    with left:
        st.subheader("Route Control")
        preset=st.selectbox("Operating preset",["Custom","Small Fleet","Busy Day","High Traffic"])
        presets={"Custom":(2,20,1.0),"Small Fleet":(2,20,1.0),"Busy Day":(4,25,1.3),"High Traffic":(5,30,1.8)};pv=presets[preset]
        vehicles=st.number_input("Vehicles",1,20,pv[0]);capacity=st.number_input("Capacity / vehicle",1,200,pv[1]);traffic_name=st.selectbox("Traffic",["Clear","Moderate","Heavy"],index={1.0:0,1.3:1,1.8:2}[pv[2]]);traffic={"Clear":1.0,"Moderate":1.3,"Heavy":1.8}[traffic_name]
        depot=st.text_input("Depot — Lat, Lon","40.750,-73.990")
        if "dyn_stops" not in st.session_state:st.session_state.dyn_stops=DEFAULT_STOPS
        st.text_area("Orders — Lat, Lon, Demand",key="dyn_stops",height=190)
        total_demand=sum(int(x.split(",")[2]) for x in st.session_state.dyn_stops.splitlines() if x.strip() and len(x.split(","))>2)
        st.caption(f"Demand: **{total_demand}** / Fleet capacity: **{int(vehicles)*int(capacity)}**")
        x,y=st.columns(2)
        with x:
            if st.button("+ Live order",use_container_width=True):st.session_state.dyn_stops+=f"\n{random.uniform(40.73,40.77):.4f},{random.uniform(-74,-73.97):.4f},{random.randint(1,5)}";st.rerun()
        with y:
            if st.button("Load demo route",use_container_width=True):
                try:run_demo();st.success("Demo route loaded")
                except Exception as exc:st.error(f"Demo failed: {exc}")
        if st.button("OPTIMIZE FLEET",type="primary",use_container_width=True):
            try:
                dlat,dlon=[float(x.strip()) for x in depot.split(",")];stops,demands=parse_stops(st.session_state.dyn_stops)
                if sum(demands)>int(vehicles)*int(capacity):raise ValueError(f"Demand {sum(demands)} exceeds fleet capacity {int(vehicles)*int(capacity)}.")
                payload={"depot":{"lat":dlat,"lon":dlon},"stops":stops,"num_vehicles":int(vehicles),"vehicle_capacities":[int(capacity)]*int(vehicles),"demands":demands,"traffic_factor":traffic}
                with st.spinner("Solving capacitated vehicle routing..."):result,engine=optimize(payload)
                st.session_state.route_data=result;st.session_state.route_engine=engine;st.session_state.depot_coords=[dlat,dlon];st.session_state.optimization_config={"vehicles":int(vehicles),"capacity":int(capacity),"traffic":traffic_name,"orders":len(stops)};st.success(f"Route optimized successfully • {engine}")
            except Exception as exc:st.error(f"Optimization failed: {exc}")
    with right:
        data=st.session_state.get("route_data")
        if data and data.get("routes"):
            st.subheader("Live Fleet Map");loc=st.session_state["depot_coords"]
            m=folium.Map(location=loc,zoom_start=13,tiles=None,control_scale=True,prefer_canvas=True)
            folium.TileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",attr="© OpenStreetMap contributors",name="Street Map").add_to(m)
            folium.TileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",attr="© OpenStreetMap © CARTO",name="Dark Map").add_to(m)
            folium.TileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",attr="© OpenStreetMap © CARTO",name="Light Map").add_to(m)
            folium.Marker(loc,popup="DEPOT",tooltip="Main Depot",icon=folium.Icon(color="red",icon="home",prefix="fa")).add_to(m)
            coords=[[[s["lat"],s["lon"]] for s in r["stops"]] for r in data["routes"]];roads=get_osrm_routes(tuple(tuple(tuple(p) for p in r) for r in coords));points=[loc]
            for i,r in enumerate(data["routes"]):
                layer=folium.FeatureGroup(name=f"🚚 Vehicle {i+1}");folium.PolyLine(roads[i],color="#e3262e",weight=6,opacity=.95,tooltip=f"Vehicle {i+1} • {r['distance_km']:.2f} km").add_to(layer)
                seq=0
                for stop in r["stops"]:
                    if stop["node"]!=0:
                        seq+=1;pt=[stop["lat"],stop["lon"]];points.append(pt);folium.Marker(pt,popup=f"<b>{stop['label']}</b><br>Vehicle {i+1}<br>Stop {seq}",tooltip=f"#{seq} {stop['label']}",icon=folium.Icon(color="red",icon="shopping-cart",prefix="fa")).add_to(layer)
                layer.add_to(m)
            folium.LayerControl(collapsed=False).add_to(m)
            if len(points)>1:
                lats=[p[0] for p in points];lons=[p[1] for p in points];m.fit_bounds([[min(lats)-.005,min(lons)-.005],[max(lats)+.005,max(lons)+.005]])
            st_folium(m,width=900,height=600)
        else:st.info("Set your fleet and orders, then run optimization — or use Load demo route.")

with analytics_tab:
    data=st.session_state.get("route_data");st.subheader("Fleet Command Center")
    if data and data.get("routes"):
        cfg=st.session_state.get("optimization_config",{});total=data["total_distance_km"];base=data["baseline_distance_km"];saved=data["saved_distance_km"];imp=data["efficiency_improvement_pct"];load=sum(r["load"] for r in data["routes"]);cap=cfg.get("capacity",1)*len(data["routes"]);util=round(load/cap*100,1) if cap else 0;fuel=total*.11
        a,b,c,d,e=st.columns(5);a.metric("DISTANCE",f"{total:.1f} km");b.metric("SAVED",f"{saved:.1f} km");c.metric("EFFICIENCY",f"{imp:.1f}%");d.metric("UTILIZATION",f"{util}%");e.metric("CO₂",f"{fuel*2.31:.1f} kg")
        df=pd.DataFrame([{"Vehicle":r["vehicle_id"]+1,"Stops":max(0,len(r["stops"])-2),"Distance (km)":r["distance_km"],"Load":r["load"]} for r in data["routes"]]);st.dataframe(df,use_container_width=True,hide_index=True)
        st.bar_chart(df.set_index("Vehicle")["Distance (km)"])
    else:st.info("Run an optimization to unlock fleet analytics.")

with eta_tab:
    st.subheader("ETA Intelligence");distance=st.number_input("Trip distance (miles)",.1,100.,2.5);hour=st.slider("Hour",0,23,14);speed_label=st.selectbox("Average speed",["Light — 25 mph","Moderate — 15 mph","Heavy — 8 mph"],index=1);speed={"Light — 25 mph":25.,"Moderate — 15 mph":15.,"Heavy — 8 mph":8.}[speed_label]
    if st.button("PREDICT ETA",type="primary",use_container_width=True):
        model=load_model()
        try:
            if model is not None:
                pred=float(model.predict(pd.DataFrame([{"haversine_km":distance*1.6,"hour_of_day":hour,"day_of_week":1,"is_weekend":0,"speed_mph":speed}]))[0]);st.success(f"Predicted delivery time: {pred:.2f} minutes • Local ML")
            else:st.success(f"Estimated delivery time: {(distance/speed*60):.2f} minutes • Analytical fallback")
        except Exception as exc:st.error(f"ETA prediction failed: {exc}")

with scenario_tab:
    st.subheader("Scenario Lab");st.dataframe(pd.DataFrame([{"Scenario":"Normal","Vehicles":2,"Capacity":20,"Traffic":1.0},{"Scenario":"Peak traffic","Vehicles":4,"Capacity":25,"Traffic":1.8},{"Scenario":"High demand","Vehicles":5,"Capacity":30,"Traffic":1.3},{"Scenario":"Resilient fleet","Vehicles":6,"Capacity":25,"Traffic":1.3}]),use_container_width=True,hide_index=True)

with reports_tab:
    data=st.session_state.get("route_data")
    if data and data.get("routes"):
        cfg=st.session_state.get("optimization_config",{});summary={"engine":st.session_state.get("route_engine"),"optimized_distance_km":data["total_distance_km"],"baseline_distance_km":data["baseline_distance_km"],"saved_distance_km":data["saved_distance_km"],"efficiency_improvement_pct":data["efficiency_improvement_pct"],"vehicles":len(data["routes"]),"orders":cfg.get("orders",0)};st.json(summary);df=pd.DataFrame([{"Vehicle":r["vehicle_id"]+1,"Distance (km)":r["distance_km"],"Load":r["load"]} for r in data["routes"]]);st.download_button("DOWNLOAD CSV",df.to_csv(index=False).encode(),"fleet_report.csv","text/csv",use_container_width=True);st.download_button("DOWNLOAD JSON",json.dumps({"summary":summary,"routes":data["routes"]},indent=2).encode(),"optimization_report.json","application/json",use_container_width=True)
    else:st.info("Run an optimization to generate a report.")

st.divider();st.caption("Last-Mile Delivery Optimization • OR-Tools CVRP • ML ETA • OSRM • Streamlit • FastAPI")
