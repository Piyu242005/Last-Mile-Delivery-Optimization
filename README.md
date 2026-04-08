<!-- HEADER -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=200&section=header&text=Last%20Mile%20Delivery%20Optimization&fontSize=40&fontAlignY=35&fontColor=ffffff&desc=High-Performance%20ML%20and%20Route%20Engine&descAlignY=55&descAlign=50" width="100%" alt="Header Image"/>

### 🚚 Predict Latency. Optimize Routes. Maximize Efficiency. 🚀

<br>

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](#)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Enabled-00FF66.svg?style=for-the-badge&logo=scikit-learn&logoColor=black)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg?style=for-the-badge&logo=github&logoColor=white)](#)

**A highly scalable logistics optimization system capable of processing 50GB+ city-scale datasets to predict delivery times using XGBoost and mathematically orchestrate routes via Google OR-Tools.**

</div>

---

## 📌 Overview

Inefficient last-mile delivery is one of the most expensive logistical hurdles, accounting for over **50% of total shipping costs**.

This project simulates a highly dense urban logistics network using massive NYC Taxi datasets (>50GB scaling capabilities) by treating taxi pickups as **warehouse dispatches** and drop-offs as **delivery destinations**. It doesn't just predict *when* a package will arrive—it determines the *exact shortest multi-stop path* required to deliver it.

---

## ✨ System Workflow

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Delivery%20Truck.png" alt="Delivery Truck Workflow" width="12%">
</div>

<br>

```text
Fetch Data ➔ Engineer Features ➔ Predict Duration ➔ Optimize Route ➔ Visual Dashboard
```

1. **Fetch Data**: Securely handle out-of-core downloads of massive Parquet/CSV datasets.
2. **Predict Duration**: The XGBoost model calculates highly accurate delivery duration estimates.
3. **Formulate VRP**: Stops are structured into a Vehicle Routing Problem (VRP) distance matrix.
4. **Optimize Route**: Google OR-Tools computes the absolute shortest distance crossing all nodes.
5. **Interactive UI**: View predicted times and interactive routing maps via Folium & Streamlit.

---

## 🚀 Key Features

| Feature | Description | Business Impact |
| :--- | :--- | :--- |
| **🎯 Duration Prediction** | XGBoost algorithm estimates travel times with a **2.98 min RMSE**. | Anticipate ETA and logistics delays. |
| **🗺️ Route Optimization** | Solves 50+ map coordinates to find shortest distances in < 2s. | Slash fuel costs and vehicle wear. |
| **⚡ Out-of-Core Processing**| Bypasses RAM constraints using smart chunk-reading workflows. | Process 50GB+ data on standard hardware. |
| **📍 Interactive Mapping** | Renders dynamic real-time map interfaces via Folium. | Visualize node paths easily. |
| **📊 Centralized Dash** | Clean, accessible Streamlit dashboard powered by FastAPI. | Enables non-technical dispatcher use. |

---

## 🛠️ Technology Stack

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-111111?style=for-the-badge&logo=xgboost&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-4285F4?style=for-the-badge&logo=google&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

</div>

---

## 📊 Evaluation & Impact

- 📈 **Model Performance**: Selected **XGBoost** for its ability to handle immense, sparse geospatial data, maintaining steady **~2.98 min** error margins.
- ⚡ **Algorithmic Throughput**: The OR-Tools VRP Solver crunches complex multi-stop matrices entirely under **2000 milliseconds**.
- 💼 **Decision Automaton**: Replaces manual dispatcher mapping with pure mathematical routing efficiency, unlocking massive time & fuel savings.

---

## ⚙️ How to Run

Launch the dashboard locally in a few steps:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download the Heavy Dataset 
# Securely fetches files into the /Dataset/ folder (Ignored by Git)
python download_data.py

# 3. Process Data & Train Model
python data/preprocess.py
python model/train.py

# 4. Fire Up the Backend API (Terminal 1)
uvicorn api.main:app --reload

# 5. Launch the Dashboard (Terminal 2)
streamlit run dashboard/app.py
```

> **Note:** The Streamlit Dashboard will start on `localhost:8501`, and the FastAPI Backend on `localhost:8000`. You can test endpoints via `http://localhost:8000/docs`.

---

## 📁 Repository Structure

```text
📦 Last-Mile-Delivery-Optimization
 ┣ 📂 api               # FastAPI backend & endpoints
 ┣ 📂 dashboard         # Streamlit interactive UI
 ┣ 📂 data              # Data processing & feature engineering logic
 ┣ 📂 model             # Model training & optimization algorithms
 ┣ 📂 notebooks         # Jupyter notebooks for EDA and prototyping
 ┣ 📜 download_data.py  # Automated script for heavy dataset management
 ┣ 📜 requirements.txt  # Project dependencies
 ┗ 📜 README.md         # Project documentation
```

---

## 🎯 Future Roadmap

- [ ] **Live Traffic API Module**: Inject genuine live-traffic data into the XGBoost Regressor.
- [ ] **Cloud Deployment**: Host directly via Render or AWS EC2 for dispatchers to test remotely.
- [ ] **Mobile Dispatch View**: Implement a responsive UI layer specifically targeting delivery drivers on duty.

---

## 💬 Let's Connect

**Piyush Ramteke**
- 💼 **LinkedIn**: [Connect with me](https://www.linkedin.com/in/piyu24)
- 💻 **GitHub**: [Piyu242005](https://github.com/Piyu242005)
- 📧 **Email**: [piyu.143247@gmail.com](mailto:piyu.143247@gmail.com)

<br>

<div align="center">
  <b>⭐ If you find this repository useful, please consider giving it a star! ⭐</b>
</div>
