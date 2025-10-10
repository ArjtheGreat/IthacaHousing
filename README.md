# IthacaInsights.com 🏠  
[Visit Here](https://ithacainsights.com/)

Ithaca Insights is a real-time dashboard for housing data in Ithaca, NY. It helps users explore rental trends, compare listings, and understand the local housing market through advanced spatial analytics and machine learning.

---

## 🎯 Features

- **Interactive Maps**: Visualize available housing listings with fair value indicators
- **ML-Powered Predictions**: Compares predicted vs. listed rents using spatial regression models
- **Smart Clustering**: Automatically groups neighborhoods by price and location
- **Comparative Market Analysis**: KNN-based rental price analysis
- **Model Evaluation**: Automatic selection of best-performing ML model (Linear, Spatial Durbin, Random Forest, XGBoost)
- **Interactive Zoning Data**: Intelligent parcel site-selection (WIP)

Ithaca Insights is designed to serve students and renters looking for a fair deal, as well as researchers and anyone looking to understand Ithaca's housing landscape without guesswork.

---

## 🏗️ Architecture

```
IthacaHousing/
├── frontend/          # Vue.js + TypeScript SPA
├── backend/           # FastAPI REST API
└── backend/airflow/   # Apache Airflow ML pipeline
```

### 📁 Project Structure

- **[Frontend README](./frontend/README.md)** - Vue.js application architecture
- **[Backend README](./backend/README.md)** - FastAPI service and database
- **[Airflow README](./backend/airflow/README.md)** - ML pipeline and data processing

---

## 💡 Why It Exists

Finding housing in Ithaca is challenging. Listings are scattered across multiple platforms, and prices vary significantly. IthacaInsights aggregates data, applies spatial machine learning models, and provides actionable insights to help renters make informed decisions.

---

## 🛠️ Tech Stack

- **Frontend**: Vue.js 3, TypeScript, Leaflet Maps, deployed via Fly.io  
- **Backend**: Python, FastAPI, PostgreSQL (Supabase), SQLAlchemy
- **ML Pipeline**: Apache Airflow, scikit-learn, XGBoost, PySAL (Spatial Analysis)
- **Data**: Real-time parsing from Ithaca rental feeds
- **Models**: Spatial Durbin, Random Forest, XGBoost with automatic model selection
- **Infrastructure**: Docker, CI/CD via GitHub Actions  
- **Monitoring**: Prometheus + Grafana metrics at `/metrics`

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL
- Docker (optional)

### Backend Setup
```bash
cd backend
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Airflow Setup
```bash
cd backend/airflow
docker-compose up -d
```

---

## 📊 Data Pipeline

1. **Data Collection**: Scrapes rental listings from Ithaca housing sources
2. **Feature Engineering**: Calculates transit scores, amenity scores, safety ratings
3. **Spatial Analysis**: Computes travel times, distances, spatial lags
4. **Model Training**: Trains and evaluates 4+ ML models, selects best performer
5. **CMA Analysis**: Performs comparative market analysis using KNN
6. **Database Update**: Stores predictions and analysis results

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 License

This project is open source and available under the MIT License.

---

## 👥 Team

Built by the Maitrix Labs team.
