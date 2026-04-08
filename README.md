<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Delivery%20Truck.png" alt="Delivery Truck" width="100"/>

  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=30&pause=1000&color=00D2FF&center=true&vCenter=true&width=800&lines=🚚+Last+Mile+Delivery+Optimization;🚀+Route+Optimization+Engine;📊+50GB%2B+Data+Processing;⚡+Powered+by+XGBoost+%26+OR-Tools" alt="Typing SVG" />
  </a>
  
  <p><i>A high-performance ML & Route Optimization engine processing massive city-scale datasets.</i></p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/XGBoost-150458?style=for-the-badge&logo=xgboost&logoColor=white" alt="XGBoost" />
    <img src="https://img.shields.io/badge/OR--Tools-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="OR-Tools" />
  </p>
</div>

<br/>

___

<details>
  <summary><b>⚡ Overview & Objective (Click to Expand)</b></summary>
  <br/>
  <p>A scalable logistics optimization system built using massive NYC Taxi datasets (>50GB scaling capabilities). By treating taxi pickups as <b>warehouse dispatches</b> and drop-offs as <b>delivery destinations</b>, this system simulates a highly dense urban logistics network, offering real-time prediction and dynamic routing to minimize delivery latency.</p>
  <blockquote>
    <b>💡 The Objective:</b> Reduce overall delivery delays by accurately predicting transit times and mathematically optimizing vehicle multi-stop routes.
  </blockquote>
</details>

<details open>
  <summary><b>🏗️ System Architecture</b></summary>
  <br/>
  
  | 🧩 Component | ⚙️ Technology | 📝 Description |
  | :--- | :--- | :--- |
  | **Data & ML Engine** | <img src="https://img.shields.io/badge/XGBoost-150458?style=flat&logo=xgboost&logoColor=white"/> | Chunk-processes large datasets out-of-core. Engineers geospatial features and trains a regressor estimating delivery durations with an **RMSE of 2.98 mins**. |
  | **Routing Engine**   | <img src="https://img.shields.io/badge/OR--Tools-4285F4?style=flat&logo=google&logoColor=white"/> | Formulates stops into a VRP (Vehicle Routing Problem) distance matrix, identifying the shortest multi-stop path in `< 2 seconds`. |
  | **Interactive UI**   | <img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white"/> | Exposes dual predictive/routing endpoints and visualizes them on a dynamic real-time map interface via Folium. |

</details>

<details>
  <summary><b>📂 Project Structure & Navigation</b></summary>

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
</details>

___

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Rocket.png" width="30" /> Getting Started

Follow these instructions to deploy the intelligent delivery system locally.

### 1️⃣ Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2️⃣ Dataset Configuration
Due to GitHub's file size limits, the massive NYC Taxi dataset (>7GB core) is not stored here. Run the automated script to securely fetch the original parquet dataset from the official [NYC TLC Trip Record](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) servers:

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

___

## <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Chart%20Increasing.png" width="30" /> Performance Highlights

- **🎯 Predictive Supremacy:** ~2.98 min error margin on vast amounts of out-of-sample data.
- **⚡ Out-of-Core Processing:** Bypasses RAM constraints utilizing smart chunk-reading workflows.
- **🗺️ Algorithmic Edge:** Generates routes factoring 50+ map coordinates to find the shortest distances in under 2000 milliseconds.

___

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Star-Struck.png" alt="Star Struck" width="40"/>
  <br/>
  <i>"Built a scalable last-mile delivery optimization system processing large datasets, improving delivery time estimations using Machine Learning (XGBoost) and optimizing delivery pathways via Google OR-Tools and FastAPI."</i>
  <br/><br/>
  <b>Built with ❤️ by <a href="https://github.com/Piyu242005">Piyu</a></b>
</div>
