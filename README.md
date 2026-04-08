<div align="center">
  <h1>🚚 Last Mile Delivery Optimization System</h1>
  <p><i>A high-performance ML & Route Optimization engine processing massive city-scale datasets.</i></p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/XGBoost-150458?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost" />
    <img src="https://img.shields.io/badge/OR--Tools-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="OR-Tools" />
  </p>
</div>

---

## ⚡ Overview

A scalable logistics optimization system built using massive NYC Taxi datasets (>50GB scaling capabilities). By treating taxi pickups as **warehouse dispatches** and drop-offs as **delivery destinations**, this system simulates a highly dense urban logistics network, offering real-time prediction and dynamic routing to minimize delivery latency.

> **💡 The Objective:** Reduce overall delivery delays by accurately predicting transit times and mathematically optimizing vehicle multi-stop routes.

---

## 🏗️ System Architecture

The solution architecture spans three critical micro-pipelines:

| 🧩 Component | ⚙️ Technology | 📝 Description |
| :--- | :--- | :--- |
| **Data & ML Engine** | `XGBoost`, `Pandas` | Chunk-processes large datasets out-of-core. Engineers geospatial features and trains a regressor estimating delivery durations with an **RMSE of 2.98 mins**. |
| **Routing Engine**   | `Google OR-Tools` | Formulates stops into a VRP (Vehicle Routing Problem) distance matrix, identifying the shortest multi-stop path in `< 2 seconds`. |
| **Interactive UI**   | `FastAPI`, `Streamlit` | Exposes dual predictive/routing endpoints and visualizes them on a dynamic real-time map interface via Folium. |

---

## 📂 Project Structure

```text
📦 Last-Mile-Delivery-Optimization
 ┣ 📂 api               # FastAPI backend & endpoints
 ┣ 📂 dashboard         # Streamlit interactive UI
 ┣ 📂 data              # Data processing & feature engineering logic
 ┣ 📂 model             # Model training & optimization algorithms
 ┣ 📂 notebooks         # Jupyter notebooks for EDA and prototyping
 ┣ 📜 download_data.py  # Automated script for heavy dataset management
 ┣ 📜 requirements.txt  # Project dependencies
 ┗ 📜 README.md         # You are here!
```

---

## 🚀 Getting Started

Follow these steps to deploy the intelligent delivery system locally.

### 1️⃣ Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2️⃣ Dataset Configuration
Due to GitHub's file size limits, the massive NYC Taxi dataset (>7GB core) is not stored here. Run the automated script to securely fetch the original parquet dataset from the official [NYC TLC Trip Record](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) servers straight into your local directory:

```bash
python download_data.py
```
*Note: A progress bar will track the download. The data will seamlessly download into `./Dataset/` which is safely ignored by Git.*

### 3️⃣ Process & Train Models
Process all data in scalable 100k-row chunks and re-train the predictive models:
```bash
# Clean & feature engineer
python data/preprocess.py

# Train XGBoost regressor & save weights
python model/train.py
```

### 4️⃣ Fire Up the Backend API
Launch the high-performance FastAPI server to expose endpoints.
```bash
uvicorn api.main:app --reload
```
> **🔗 API Running at:** `http://localhost:8000`  
> **📚 Swagger UI Docs:** `http://localhost:8000/docs`

### 5️⃣ Launch the Control Center
Start the Streamlit deployment dashboard in a separate terminal.
```bash
streamlit run dashboard/app.py
```
> **🖥️ Dashboard Running at:** `http://localhost:8501`

---

## 📸 Performance Highlights

- **Predictive Supremacy:** ~2.98 min error margin on vast amounts of out-of-sample data.
- **Out-of-Core Processing:** Bypasses RAM constraints utilizing smart chunk-reading workflows.
- **Algorithmic Edge:** Generates routes factoring 50+ map coordinates to find the shortest distances in under 2000 milliseconds.

---

> 💻 **Resume Highlight:** *"Built a scalable last-mile delivery optimization system processing large datasets, improving delivery time estimations using Machine Learning (XGBoost) and optimizing delivery pathways via Google OR-Tools and FastAPI."*

---
<div align="center">
  <b>Built by Piyu</b>
</div>
