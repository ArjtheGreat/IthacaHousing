# Airflow ML Pipeline 🤖

Apache Airflow-based machine learning pipeline for automated housing data processing, feature engineering, and model training.

---

## 📁 File Structure

```
airflow/
├── dags/                           # Airflow DAGs
│   └── housing_data_training.py   # Main ML pipeline DAG
├── model/                          # ML modules
│   ├── __init__.py
│   ├── pipeline.py                # Main pipeline orchestrator
│   ├── fetch_housing_data.py      # Data collection
│   ├── data_preprocessing.py      # Data cleaning & transformation
│   ├── calculate_travel_times_distance.py  # Route calculations
│   ├── calculate_transit_score.py # Transit accessibility
│   ├── calculate_amenity_score.py # Nearby amenities
│   ├── extract_safety_features.py # Safety ratings
│   ├── model_training.py          # ML model training & evaluation
│   ├── comparative_market_analysis.py  # CMA analysis
│   ├── spatial_regression.py      # Spatial regression models
│   └── insert_into_postgredb.py   # Database operations
├── logs/                           # Airflow logs
├── airflow.cfg                     # Airflow configuration
├── docker-compose.yml              # Docker setup
├── dockerfile                      # Airflow container
├── requirements.txt                # Python dependencies
└── webserver_config.py            # Webserver configuration
```

---

## 🏗️ Pipeline Architecture

### Data Flow

```
1. Data Collection
   ├── Fetch Housing Listings
   └── Geocode Addresses

2. Feature Engineering
   ├── Calculate Travel Times (Walk/Bike/Drive)
   ├── Calculate Transit Score
   ├── Calculate Amenity Score
   └── Extract Safety Features

3. Data Preprocessing
   ├── Handle Missing Values (Median/Mode Imputation)
   ├── Log Transform Prices
   └── Outlier Detection

4. Model Training & Evaluation
   ├── Define Features (X) & Target (y)
   ├── Create Spatial Features
   ├── Train 4 Models:
   │   ├── Linear Regression (Spatial)
   │   ├── Spatial Durbin Model
   │   ├── Random Forest (Spatial)
   │   └── XGBoost (Spatial)
   ├── Evaluate Models (RMSE, R², MAPE)
   ├── Select Best Model
   └── Generate Predictions

5. Comparative Market Analysis
   ├── Define Features for CMA
   ├── KNN-based Price Analysis
   └── Find Nearest Neighbors

6. Database Update
   ├── Serialize Data
   ├── Handle Type Conversions
   └── Insert into PostgreSQL
```

---

## 🔧 Model Training Pipeline

### Model Evaluation Workflow

The pipeline implements an intelligent model selection system:

```python
# 1. Train multiple models
models = {
    "LinearRegression (Spatial)": train_linear_model,
    "Spatial Durbin": ml_durbin_model,
    "RandomForest (Spatial)": spatial_random_forest_regressor,
    "XGBoost (Spatial)": spatial_xgboost_regressor
}

# 2. Evaluate each model
for model_name, model_func in models.items():
    predictions = model_func(X, y, data)
    rmse = calculate_rmse(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)
    mape = calculate_mape(y_true, y_pred)

# 3. Flag overfitting models (R² > 0.95)
if r2 > 0.95:
    flagged = True

# 4. Select best model
best_model = select_best_model(
    results,
    r2_weight=0.5,
    rmse_weight=0.5
)

# 5. Use best model for predictions
```

### Feature Engineering

#### X (Features)
```python
[
    "LengthAvailable",           # Lease length
    "Pets",                      # Pet policy
    "combined_bedrooms_bathrooms", # Bed + Bath count
    "drive_time",                # Drive time to Cornell
    "transit_score",             # Transit accessibility
    "amenities_score",           # Nearby amenities
    "OverallSafetyRating"        # Safety rating
]
```

#### y (Target)
```python
"RentAmountAdjusted"  # Log-transformed rent
```

### Spatial Features

The pipeline creates spatial lag features using K-Nearest Neighbors:

```python
# For each feature, create spatial lag
W_LengthAvailable = spatial_lag(knn_weights, LengthAvailable)
W_Pets = spatial_lag(knn_weights, Pets)
# ... etc
```

This captures spatial autocorrelation in housing markets.

---

## 🤖 Machine Learning Models

### 1. Linear Regression (Spatial)
```python
# OLS with spatial lag features
X_spatial = add_spatial_lags(X, k=5)
model = OLS(y, add_constant(X_spatial))
```

**Use Case**: Baseline interpretable model

### 2. Spatial Durbin Model
```python
# Maximum Likelihood spatial regression
sdm_model = ML_Lag(
    y, X, w=knn_weights,
    slx_lags=1  # Spatial lag of X
)
```

**Use Case**: Captures spatial spillover effects

### 3. Random Forest (Spatial)
```python
rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    random_state=42
)
rf.fit(X_spatial, y)
```

**Use Case**: Non-linear relationships, feature importance

### 4. XGBoost (Spatial)
```python
xgb = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=8,
    subsample=0.8,
    colsample_bytree=0.8
)
xgb.fit(X_spatial, y)
```

**Use Case**: Best performance, handles complex patterns

---

## 📊 Model Evaluation Metrics

### RMSE (Root Mean Squared Error)
```python
rmse = sqrt(mean((y_true - y_pred)²))
```
- Lower is better
- Penalizes large errors
- Same units as target variable

### R² (Coefficient of Determination)
```python
r2 = 1 - (SSE / SST)
```
- Range: 0 to 1
- Measures variance explained
- Higher is better (but watch for overfitting)

### MAPE (Mean Absolute Percentage Error)
```python
mape = mean(|y_true - y_pred| / y_true) * 100
```
- Percentage error
- Easy to interpret
- Lower is better

### Overfitting Detection
```python
if r2 > 0.95:
    flag_as_overfit()
```

---

## 🔄 Data Preprocessing

### Missing Value Imputation

```python
def median_mode_imputation(X):
    # Numeric: Fill with median
    # Categorical: Fill with mode
    return X_filled
```

### Log Transformation

```python
def log_transform_prices(y):
    # Natural log of rent prices
    # Normalizes distribution
    return np.log(y)
```

### Type Conversion

```python
def clean_data(X):
    # Convert to numeric
    # Handle inf/nan values
    # Ensure float64 type
    return X_clean
```

---

## 🏘️ Comparative Market Analysis (CMA)

### KNN-based Analysis

```python
# 1. Define features including coordinates
X_cma = [
    "LengthAvailable", "Pets", 
    "combined_bedrooms_bathrooms",
    "drive_time", "transit_score",
    "amenities_score", "OverallSafetyRating",
    "GmapLatitude", "GmapLongitude"
]

# 2. Find K nearest neighbors (K=4)
nbrs = NearestNeighbors(n_neighbors=4)
nbrs.fit(X_cma)

# 3. Predict rent as average of neighbors
predicted_rent = mean(neighbor_rents)
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.12+
- Apache Airflow 2.10+
- PostgreSQL

### Installation

```bash
cd backend/airflow

# Create virtual environment
python -m venv myenv
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start webserver
airflow webserver -p 8080

# Start scheduler (in another terminal)
airflow scheduler
```

### Docker Setup

```bash
docker-compose up -d
```

Access Airflow UI: `http://localhost:8080`

---

## 📅 DAG Configuration

### housing_data_training.py

```python
dag = DAG(
    'retrain_rental_model',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
    },
    description='Housing data ML pipeline',
    schedule_interval='0 0 * * 0',  # Weekly
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

task = PythonOperator(
    task_id='run_housing_pipeline',
    python_callable=housing_data_pipeline,
    dag=dag,
)
```

**Schedule**: Runs every Sunday at midnight

---

## 📈 Monitoring & Logging

### Airflow Logs

```bash
# View logs
tail -f logs/scheduler/latest/*.log

# DAG processor logs
tail -f logs/dag_processor_manager/*.log
```

### Model Performance Logs

```
🏆 Champion model: XGBoost (Spatial)

Model Performance Summary:
                         R2    RMSE   MAPE  Score
XGBoost (Spatial)      0.82   0.15   8.2%  0.91
RandomForest (Spatial) 0.79   0.17   9.1%  0.88
Spatial Durbin         0.76   0.19   10.3% 0.84
LinearRegression       0.71   0.22   12.1% 0.79
```

---

## 🗄️ Database Operations

### Insert Pipeline

```python
def psql_insert_copy(df):
    # 1. Convert LineString to WKT
    df['walk_routes'] = df['walk_routes'].apply(lambda x: x.wkt)
    
    # 2. Convert boolean fields
    df['HasValidCertificate'] = df['HasValidCertificate'].astype(bool)
    
    # 3. Select columns
    df = df[columns_list]
    
    # 4. Normalize column names
    df.columns = df.columns.str.lower().str.replace(...)
    
    # 5. Truncate and insert
    with engine.begin() as conn:
        conn.execute("TRUNCATE TABLE housing_listings")
        df.to_sql("housing_listings", con=conn, if_exists="append")
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Airflow
AIRFLOW_HOME=/path/to/airflow
AIRFLOW__CORE__EXECUTOR=SequentialExecutor
AIRFLOW__CORE__LOAD_EXAMPLES=False

# Database
DB_URI=postgresql://user:pass@host:port/dbname

# APIs
GOOGLE_PLACES_API_KEY=your_key_here
```

### Airflow Config

Key settings in `airflow.cfg`:
```ini
[core]
executor = SequentialExecutor
load_examples = False

[webserver]
web_server_port = 8080
```

---

## 🧪 Testing

```bash
# Test individual modules
python -m pytest model/test_*.py

# Test DAG validity
airflow dags test retrain_rental_model

# Manual trigger
airflow dags trigger retrain_rental_model
```

---

## 📊 Performance Metrics

### Pipeline Runtime
- Data Collection: ~2-5 min
- Feature Engineering: ~3-7 min
- Model Training: ~5-10 min
- CMA Analysis: ~2-3 min
- Total: ~15-25 min

### Model Performance (Typical)
- RMSE: 0.12 - 0.20
- R²: 0.75 - 0.85
- MAPE: 7% - 12%

---

## 🛠️ Troubleshooting

### Common Issues

**Import Errors**
```bash
# Add model directory to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/airflow/model"
```

**Database Connection**
```bash
# Verify DB_URI in .env
echo $DB_URI

# Test connection
python -c "from db import engine; print(engine)"
```

**Module Not Found**
```bash
# Install missing package
pip install <package_name>
```

---

## 🚧 Future Enhancements

- [ ] Hyperparameter tuning with Optuna
- [ ] Model versioning with MLflow
- [ ] A/B testing framework
- [ ] Real-time predictions API
- [ ] Automated retraining triggers
- [ ] Feature importance analysis
- [ ] SHAP values for interpretability
- [ ] Model drift detection

---

## 📚 Dependencies

### Core ML Libraries
- `scikit-learn` - ML algorithms
- `xgboost` - Gradient boosting
- `statsmodels` - Statistical models
- `spreg` - Spatial regression (PySAL)
- `libpysal` - Spatial analysis

### Data Processing
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `geopandas` - Spatial data

### Airflow
- `apache-airflow` - Workflow orchestration
- `psycopg2` - PostgreSQL adapter

---

## 🤝 Contributing

1. Add new models in `model_training.py`
2. Update `evaluate_models()` dictionary
3. Test with sample data
4. Document model parameters
5. Submit PR with results

---

## 📖 References

- [Spatial Econometrics](https://pysal.org/spreg/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Apache Airflow](https://airflow.apache.org/)
- [Scikit-learn](https://scikit-learn.org/)

---
