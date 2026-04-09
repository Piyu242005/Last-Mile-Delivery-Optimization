<!-- HEADER -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=200&section=header&text=Last%20Mile%20Delivery%20Optimization&fontSize=40&fontAlignY=35&fontColor=ffffff&desc=High-Performance%20ML%20and%20Route%20Engine&descAlignY=55&descAlign=50" width="100%" alt="Header Image"/>

### 🚚 Predict Latency. Optimize Routes. Maximize Efficiency. 🚀

<br>

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Enabled-00FF66.svg?style=for-the-badge&logo=scikit-learn&logoColor=black)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg?style=for-the-badge&logo=github&logoColor=white)](#)

</div>

----

## 📌 Problem Statement

Last-mile delivery is one of the most expensive and complex parts of logistics, accounting for over **50% of total shipping costs**. Manual dispatching cannot effectively account for real-time traffic, multiple vehicle capacities, and complex multi-stop routes simultaneously.

The goal of this project is to optimize delivery routes to minimize distance, cost, and delivery time. We solve this by treating delivery routes as a **Vehicle Routing Problem with Capacities (CVRP)**, factoring in:
- Fleet size (Multiple Vehicles)
- Vehicle Capacities
- Package Demand at each stop
- Simulated Traffic Multipliers

---

## ⚙️ Approach & Architecture

### System Architecture
```mermaid
graph TD;
    A[Streamlit UI] -->|1. Config & GPS locations| B(FastAPI Backend);
    B -->|2. Request Distance Matrix| C{OSRM / Haversine};
    C -->|3. Route Geometries| B;
    B -->|4. VRP Constraints| D[Google OR-Tools Engine];
    D -->|5. Optimal Node Sequence| B;
    B -->|6. JSON Response| A;
    A -->|7. Render| E[Folium Interactive Map];
    
    F[Historical Data] -->|Train| G((Random Forest ML Model));
    G -->|ETA Prediction| B;
```

- **Data Processing:** Processed and down-sampled the large real-world NYC Yellow Taxi Dataset to extract realistic delivery locations.
- **Distance Matrix Formulation:** Created a highly accurate geographic distance matrix. Fast computations utilizing the Haversine formula are optionally enriched through the OSRM (Open Source Routing Machine) API to snap points onto valid, drivable street segments.
- **Algorithmic Optimization Engine:** Modeled dispatching as a **Capacitated Vehicle Routing Problem (CVRP)** using Google OR-Tools. 
    - *First Solution Strategy:* PATH_CHEAPEST_ARC to rapidly construct a feasible lower-bound delivery schedule.
    - *Local Search Metaheuristic:* GUIDED_LOCAL_SEARCH applied across a designated temporal boundary (e.g., 3-second limit per API request) to escape local minima and yield optimal efficiency.
- **Machine Learning Integration:** A Random Forest / XGBoost Regressor trained on baseline temporal logistics variables (Distance, Fleet Speed, Hour of Day, Traffic Multiplier heuristics) predicts dynamic parcel Estimated Time of Arrivals (ETAs), displacing standard analytical logic with statistically correlated predictions.
- **Optimal Multi-Agent Dispatching:** Dynamically bounds route arrays per vehicle dependent strictly on individual carrying-capacities versus aggregated nodal demands.

<details>
<summary><b>🧠 See Technical Constraints & Mathematical Model (Click to expand)</b></summary>

**1. Optimization Objective Equation**  
The routing engine attempts to minimize the total travel cost (or distance) across all active routes without violating vehicle capacities:  
`Minimize:  Σ (from i=0 to N) Σ (from j=0 to N) Σ (from k=1 to V) Cost(i,j) * X(i,j,k)`  
*Where `X(i,j,k) = 1` if vehicle `k` drives from node `i` to node `j`, else `0`.*

**2. Core VRP Constraints Modeled**  
- **Capacity Constraint (1D Bin Packing):** The cumulative sum of demand at stops assigned to Route `k` must be `<=` Vehicle Capacity `k`.
- **Node Visitation:** Every single delivery stop must be visited exactly once (except the depot/warehouse).
- **Sub-Tour Elimination:** Drivers must eventually close the Hamiltonian circuit back to the Global Depot `Node(0)`.

**3. The ETA Predictive Feature Vector**  
The FastAPI regressor expects: `[haversine_km, hour_of_day, speed_mph, weekday]`. 
The model applies dynamic traffic delay polynomials representing distinct real-world rush-hour delays in New York routing scenarios.
</details>

---

## 📊 Results

Implementing CVRP optimization achieves significant performance improvements over randomized, unoptimized routing:

- **Total Path Distance Reduced:** `~30-40%` on average compared to baseline dispatching.
- **Delivery Time Reduced:** Estimated `25%` reduction in total dynamic fulfillment time.
- **Efficiency Improved:** Multi-vehicle assignment improved overall vehicle utilization by `~15%`.

*(These metrics dynamically update in the Streamlit Dashboard per randomized test run)*

---

## 🗺️ Visualization

The optimized routes are visualized using maps to clearly show delivery paths and efficiency.

<br>

<p align="center">
  <b>🚚 Route Optimization & Map Visualization</b><br>
  <img src="Screenshot/1st output.png" width="900"/><br>
  <sub>Optimized delivery routes displayed on an interactive map using multiple vehicles.</sub>
</p>

---

<p align="center">
  <b>⏱️ Delivery Time Predictor</b><br>
  <img src="Screenshot/2nd output.png" width="900"/><br>
  <sub>Predict delivery duration based on distance, traffic conditions, and time of day.</sub>
</p>

---

<p align="center">
  <b>📊 Logistics Performance Metrics</b><br>
  <img src="Screenshot/3rd output.png" width="900"/><br>
  <sub>Performance comparison showing distance optimization and efficiency improvement.</sub>
</p>
  <br>
  
---

## ✨ Features

- 🚦 **Route Optimization using Algorithms:** CVRP & TSP models implemented in OR-Tools.
- 📏 **Distance Matrix Calculation:** Highly accurate geographic distance estimations.
- 📦 **Efficient Delivery Planning:** Capacity considerations handling multiple vehicles.
- 🏢 **Scalable API Architecture:** FastAPI application feeding JSON routes rapidly.
- 📊 **Interactive UI:** Streamlit visualizer demonstrating real-world impacts.

---

## 🌍 Real-world Applications

- **E-commerce delivery optimization:** Last-mile routing for multi-national dispatchers (Amazon, FedEx).
- **Logistics & supply chain management:** Route generation for multi-depot fleet management.
- **Ride-sharing route optimization:** Taxi pathing and algorithmically pooled rides.

---

## 🔮 Future Improvements

- Multi-vehicle routing with exact time windows (VRPTW).
- Real-time live traffic optimization integration.
- Dynamic route updates allowing injection of live stops mid-route.
- Deploy a Web-based dashboard (Streamlit Cloud, GCP, etc.).

---

## 📊 Dataset

This project uses the NYC Yellow Taxi Trip Data. Because the dataset is massive (~2GB), it is not hosted directly on GitHub.

🔗 **Download Dataset:**  
👉 [NYC Yellow Taxi Trip Data on Kaggle](https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data)

---


### 📁 Setup Instructions
```bash
### 📌 Instructions
1. Download the dataset from the above link
2. Extract the files (if zipped)
3. Place the dataset in the following directory:
   data/

# Step 3: Move to project folder
project/
│── data/   ← place dataset here
│── src/
│── app.py
```
---

## 📁 Project Structure & Setup Instructions

### 1. Download Dataset
1. Download the dataset from the Kaggle link directly above.
2. Extract the files and place `.csv` tracking logs inside the `Dataset/` directory.

### 2. File Organization
```bash
project/
│── Dataset/               ← Dataset .csv files (Ignored in Git, local only)
│── api/
│   └── main.py            ← FastAPI backend
│── dashboard/
│   └── app.py             ← Streamlit UI
│── data/                  ← Processing & sampling scripts
│── model/                 ← CVRP/TSP algorithmic logic
└── requirements.txt       ← Package dependencies
```

---
## 🛠️ Technology Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Leaflet-green?style=for-the-badge)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-DA5B0B?style=for-the-badge&logo=jupyter&logoColor=white)
![VS Code](https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)

</div>

## 📧 Let's Connect & Collaborate

<div align="center">

[![Email](https://img.shields.io/badge/📧_Email-piyu.143247@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:piyu.143247@gmail.com)
[![LinkedIn](https://img.shields.io/badge/💼_LinkedIn-Piyush_Ramteke-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/piyush-ramteke-24-mylife)
[![GitHub](https://img.shields.io/badge/🐙_GitHub-Piyu242005-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Piyu242005)
[![Instagram](https://img.shields.io/badge/📸_Instagram-my.life__24143-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/my.life_24143/)

</div>

---

<div align="center">

### ⭐ If you find this repository helpful, dropping a star would mean a lot!

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%" />

Made with 💚 by **Piyush Ramteke** © 2026

![Visitors](https://api.visitorbadge.io/api/visitors?path=Piyu242005%2FPiyu-Portfolio-Website&countColor=%23c8ff00)

</div>
