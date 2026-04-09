<!-- HEADER -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=200&section=header&text=Last%20Mile%20Delivery%20Optimization&fontSize=40&fontAlignY=35&fontColor=ffffff&desc=High-Performance%20ML%20and%20Route%20Engine&descAlignY=55&descAlign=50" width="100%" alt="Header Image"/>

### 🚚 Predict Latency. Optimize Routes. Maximize Efficiency. 🚀

<br>

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Enabled-00FF66.svg?style=for-the-badge&logo=scikit-learn&logoColor=black)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg?style=for-the-badge&logo=github&logoColor=white)](#)

**A highly scalable logistics optimization system solving real-world routing challenges with Advanced Vehicle Routing Problem (VRP) constraints, dynamic traffic factors, and interactive deployment dashboards.**

</div>

---

## 📌 Problem Statement

Inefficient last-mile delivery is one of the most expensive logistical hurdles, accounting for over **50% of total shipping costs**. Manual dispatching cannot account for real-time traffic, multiple vehicle capacities, and complex multi-stop routes simultaneously.

This project solves this by treating delivery drops as a **Vehicle Routing Problem with Capacities (CVRP)**, accounting for:
- Fleet size (Multiple Vehicles)
- Vehicle Capacities
- Package Demand at each stop
- Simulated Traffic Multipliers
---

## 📂 Dataset

This project uses a large dataset (~2GB) which exceeds GitHub's file size limits.

To ensure smooth access, the dataset is hosted externally.

🔗 **Download Dataset:**  
https://your-google-drive-link

### 📁 Setup Instructions
```bash
# Step 1: Download dataset
# Step 2: Extract files

# Step 3: Move to project folder
project/
│── data/   ← place dataset here
│── src/
│── app.py

## ✨ The Solution & Approach

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Delivery%20Truck.png" alt="Delivery Truck Workflow" width="12%">
</div>

Using **Google OR-Tools** and a highly responsive **FastAPI + Streamlit** stack, we dynamically generate dispatch commands:
1. **Fetch & Ingest**: Process coordinates and demand values interactively.
2. **Formulate CVRP**: Calculate a traffic-weighted Haversine distance matrix. Set up nodes, arcs, and capacities.
3. **Route Construction**: The OR-Tools local search metaheuristic computes the absolute shortest distance distributing packages across multiple drivers in seconds.
4. **Interactive Mapping**: Routes are projected directly onto stunning Folium maps with individual driver colors.

---

## 🚀 Key Features and Metrics

- **🌍 Immersive Visualization**: Fully interactive map indicating depots, stops (with cargo demands), and individual vehicle routes color-coded for clarity using Leaflet/Folium.
- **🚚 Fleet & Capacity Logistics (CVRP)**: Transitioned from basic TSP to advanced CVRP. Dispatchers can specify the number of vehicles and exactly how much cargo each can carry.
- **🚦 Traffic Simulation**: Simulate clear, moderate, or heavy delays dynamically updating distances and ETAs.
- **📈 Advanced Analytics Engine**: Instantly compare unoptimized "baseline" distance against optimized VRP distance. See straight numerical proof of efficiency gains (e.g., 30-40% distance reduction).

---

## 🛠️ Technology Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Leaflet-green?style=for-the-badge)

</div>

---

## 📊 Dataset

This project uses the NYC Yellow Taxi Trip Data. You can download the dataset from Kaggle:
👉 [NYC Yellow Taxi Trip Data](https://www.kaggle.com/datasets/elemento/nyc-yellow-taxi-trip-data)

Ensure to place the downloaded dataset files into the `Dataset/` directory before running the system.

---

## ⚙️ How to Run

Launch the dashboard locally in two terminals:

`ash
# Terminal 1: Run the Backend API Engine
pip install fastapi uvicorn ortools haversine folium streamlit-folium pydantic
python -m uvicorn api.main:app --reload

# Terminal 2: Connect the Dashboard
python -m streamlit run dashboard/app.py
`

> **Note:** Open localhost:8501. Test API directly at http://localhost:8000/docs.
