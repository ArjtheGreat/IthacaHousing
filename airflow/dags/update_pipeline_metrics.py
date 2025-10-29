from airflow.decorators import dag, task
from pendulum import datetime, duration
import sys
import os
import pandas as pd
import numpy as np
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from prometheus_client import Counter, Summary, push_to_gateway

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = __file__.decode('utf-8') if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import pipeline_metrics
import model_training
import data_preprocessing

os.environ['NO_PROXY'] = '*'

DAG_SUCCESS = Counter("dag_success_total", "Total successful DAG runs", ["dag_id"])
DAG_FAILURE = Counter("dag_failure_total", "Total failed DAG runs", ["dag_id"])
DAG_DURATION = Summary("dag_duration_seconds", "DAG execution duration in seconds", ["dag_id"])
PUSHGATEWAY_URL = "http://localhost:9091"  

def on_success_callback(context):
    dag_id = context["dag"].dag_id
    DAG_SUCCESS.labels(dag_id=dag_id).inc()
    duration = context["dag_run"].end_date - context["dag_run"].start_date
    DAG_DURATION.labels(dag_id=dag_id).observe(duration.total_seconds())
    push_to_gateway(PUSHGATEWAY_URL, job=dag_id, registry=None)  

def on_failure_callback(context):
    dag_id = context["dag"].dag_id
    DAG_FAILURE.labels(dag_id=dag_id).inc()
    push_to_gateway(PUSHGATEWAY_URL, job=dag_id, registry=None)


def fetch_housing_listings():
    """
    Fetch only the columns needed for pipeline metrics from the database
    Avoids JSON columns that cause Arrow conversion errors
    """
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        raise ValueError("DB_URI environment variable not set")
    
    engine = create_engine(DB_URI)
    
    try:
        with engine.connect() as conn:
            # Only fetch columns needed for metrics calculations
            # Based on what pipeline_metrics functions actually use:
            required_columns = [
                'listingid',
                'longitude',
                'latitude', 
                'rent_per_person',
                'predictedrent',
                'differenceinfairvalue',
                'owner_name',
                'neighborhood'
            ]
            
            # Build query with only needed columns
            select_clause = ', '.join([f'"{col}"' for col in required_columns])
            query = text(f'SELECT {select_clause} FROM housing_listings')
            
            # Use pandas read_sql
            df = pd.read_sql(query, conn)
            
            print(f"📊 Fetched {len(df)} listings with required columns from housing_listings")
            
            return df
    except Exception as e:
        print(f"❌ Error fetching housing listings: {e}")
        import traceback
        traceback.print_exc()
        raise


def fetch_latest_model_results():
    """
    Fetch the latest model_performance and feature_importance JSON directly from rental_model_runs
    Returns: tuple of (model_performance dict, feature_importance dict)
    """
    DB_URI = os.getenv("DB_URI")
    if not DB_URI:
        raise ValueError("DB_URI environment variable not set")
    
    engine = create_engine(DB_URI)
    
    try:
        with engine.connect() as conn:
            # Get the latest model_performance and feature_importance JSON
            query = text("""
                SELECT model_performance, feature_importance, run_timestamp
                FROM rental_model_runs
                WHERE model_performance IS NOT NULL
                ORDER BY run_timestamp DESC
                LIMIT 1
            """)
            result = conn.execute(query)
            row = result.fetchone()
            
            if not row:
                print("⚠️ No model results found in rental_model_runs")
                return None, None
            
            model_perf_str = row[0]
            feature_imp_str = row[1]
            run_timestamp = row[2]
            
            print(f"📊 Using model performance from {run_timestamp}")
            
            # Parse the JSON - this is already the complete model_performance dict
            model_perf = json.loads(model_perf_str) if isinstance(model_perf_str, str) else model_perf_str
            feature_imp = None
            if feature_imp_str:
                feature_imp = json.loads(feature_imp_str) if isinstance(feature_imp_str, str) else feature_imp_str
            
            if not model_perf:
                print("⚠️ Model performance data is empty")
                return None, None
            
            print(f"✅ Found model performance with best model: {model_perf.get('best_model', 'N/A')}")
            if feature_imp:
                print(f"✅ Found feature importance data")
            else:
                print("⚠️ No feature importance data found")
            
            return model_perf, feature_imp
            
    except Exception as e:
        print(f"❌ Error fetching model results: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def prepare_data_for_metrics(df):
    """
    Prepare the dataframe for metrics calculation
    Ensures required columns exist and are in the right format
    """
    # Ensure required columns exist
    required_cols = ['longitude', 'latitude', 'rent_per_person']
    
    for col in required_cols:
        if col not in df.columns:
            # Try alternative column names
            alt_names = {
                'longitude': ['longitude', 'lon', 'lng'],
                'latitude': ['latitude', 'lat'],
                'rent_per_person': ['rent_per_person', 'rentperperson', 'rent_per_person']
            }
            
            if col in alt_names:
                for alt in alt_names[col]:
                    if alt in df.columns:
                        df = df.rename(columns={alt: col})
                        break
                else:
                    raise ValueError(f"Required column '{col}' not found in dataframe")
    
    # Ensure coordinates are numeric
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    
    # Drop rows with missing coordinates
    df = df.dropna(subset=['longitude', 'latitude'])
    
    # Ensure rent_per_person is numeric
    df['rent_per_person'] = pd.to_numeric(df['rent_per_person'], errors='coerce')
    
    print(f"📊 Prepared {len(df)} listings with valid coordinates and rent data")
    
    return df


def compute_metrics_with_model_performance(apartments_for_rent, model_perf_dict, feature_imp_dict=None):
    """
    Compute pipeline metrics using the existing model_performance from database
    No need to recompute model metrics - just plug in what we have
    """
    try:
        import geopandas as gpd
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            apartments_for_rent,
            geometry=gpd.points_from_xy(apartments_for_rent.longitude, apartments_for_rent.latitude),
            crs="EPSG:4326"
        )
        
        # Debug: Check if differenceinfairvalue column exists and has data
        if "differenceinfairvalue" not in apartments_for_rent.columns:
            print("⚠️ WARNING: 'differenceinfairvalue' column not found in apartments_for_rent")
            print(f"📋 Available columns: {apartments_for_rent.columns.tolist()}")
        else:
            null_count = apartments_for_rent["differenceinfairvalue"].isna().sum()
            total_count = len(apartments_for_rent)
            print(f"📊 differenceinfairvalue: {total_count - null_count} non-null values out of {total_count} total")
            if null_count == total_count:
                print("⚠️ WARNING: All values in 'differenceinfairvalue' are null!")
        
        # Compute all the metrics that depend on current listings
        lisa_result = pipeline_metrics.compute_lisa_for_each_point(apartments_for_rent)
        if lisa_result is None:
            print("⚠️ WARNING: compute_lisa_for_each_point returned None")
            if "differenceinfairvalue" not in apartments_for_rent.columns:
                print("   Reason: 'differenceinfairvalue' column is missing")
            elif apartments_for_rent["differenceinfairvalue"].isna().all():
                print("   Reason: All 'differenceinfairvalue' values are null")
        
        analysis = {
            "spatial_patterns": pipeline_metrics.compute_spatial_patterns(apartments_for_rent),
            "lisa_for_each_point": lisa_result,
            "landlord_behavior": pipeline_metrics.analyze_landlords(gdf),
            "overpricing": pipeline_metrics.analyze_overpricing(gdf),
            # Just use the model_performance from the database - no need to recompute
            "model_performance": model_perf_dict,
            # Use feature_importance from database if available
            "feature_importance": feature_imp_dict
        }
        
        # Serialize pandas objects before returning (for XCom)
        # This converts pandas Series, DataFrames, numpy types to JSON-serializable formats
        analysis = pipeline_metrics.serialize_metrics(analysis)
        
        # Additional safety: ensure no pandas objects remain
        def ensure_serializable(obj):
            """Recursively ensure no pandas objects remain"""
            if isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, dict):
                return {k: ensure_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [ensure_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj) if isinstance(obj, np.floating) else int(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        analysis = ensure_serializable(analysis)
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error computing metrics: {e}")
        import traceback
        traceback.print_exc()
        raise


@dag(
    dag_id="update_pipeline_metrics",
    start_date=datetime(2025, 3, 30),
    schedule="0 */6 * * *",  # Every 6 hours
    catchup=False,
    description="Update pipeline metrics from existing housing_listings and model results",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    on_success_callback=on_success_callback,
    on_failure_callback=on_failure_callback,
    tags=["housing", "metrics", "analytics"]
)
def update_pipeline_metrics():
    
    @task(
        retries=1,
        execution_timeout=duration(minutes=5)
    )
    def fetch_listings():
        """Fetch housing listings from database"""
        return fetch_housing_listings()

    @task(
        retries=1,
        execution_timeout=duration(minutes=2)
    )
    def fetch_model_results():
        """Fetch latest model results from rental_model_runs"""
        return fetch_latest_model_results()

    @task(
        execution_timeout=duration(minutes=10)
    )
    def compute_metrics(**context):
        """Compute pipeline metrics from listings and use existing model results"""
        ti = context['ti']
        
        # Get data from previous tasks
        listings_df = ti.xcom_pull(task_ids='fetch_listings')
        model_results = ti.xcom_pull(task_ids='fetch_model_results')
        
        # Unpack model results (returns tuple of (model_perf_dict, feature_imp_dict))
        if model_results and isinstance(model_results, tuple):
            model_perf_dict, feature_imp_dict = model_results
        else:
            model_perf_dict = None
            feature_imp_dict = None
        
        # Prepare listings data
        apartments_for_rent = prepare_data_for_metrics(listings_df)
        
        # If no model results, create a minimal placeholder
        if model_perf_dict is None:
            print("⚠️ No model results found, using placeholder")
            model_perf_dict = {
                "best_model": "Unknown Model",
                "best_model_metrics": {
                    "R2": 0.0,
                    "RMSE": 0.0,
                    "MAPE": 0.0
                },
                "all_model_results": {},
                "random_forest_results": None,
                "linear_regression_results": None,
                "spatial_durbin_results": None
            }
        
        # Compute metrics (using existing model_performance and feature_importance, not recomputing)
        analysis = compute_metrics_with_model_performance(
            apartments_for_rent, 
            model_perf_dict,
            feature_imp_dict
        )
        
        return analysis

    @task(
        execution_timeout=duration(minutes=2)
    )
    def insert_metrics(**context):
        """Insert computed metrics into rental_model_runs"""
        ti = context['ti']
        analysis = ti.xcom_pull(task_ids='compute_metrics')
        
        if analysis:
            pipeline_metrics.insert_pipeline_metrics(analysis)
            print("✅ Pipeline metrics inserted successfully")
        else:
            print("⚠️ No metrics to insert")

    # Task dependencies
    listings_result = fetch_listings()
    model_result = fetch_model_results()
    metrics_result = compute_metrics()
    insert_result = insert_metrics()
    
    # Run fetch tasks in parallel, then compute and insert
    [listings_result, model_result] >> metrics_result >> insert_result


# Instantiate the DAG
update_pipeline_metrics()

