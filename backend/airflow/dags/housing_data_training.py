from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import pandas as pd
import sys
import os
import numpy as np
from pathlib import Path 
from prometheus_client import Counter, Summary, push_to_gateway

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = str(__file__) if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import fetch_housing_data
import pipeline
import insert_into_postgredb

fetch_active_listings = fetch_housing_data.fetch_active_listings
housing_data_pipeline = pipeline.housing_data_pipeline
confirmation = insert_into_postgredb.confirmation

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


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 3, 30),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "retrain_rental_model",
    default_args=default_args,
    description="Fetch rental listings and retrain model",
    schedule_interval="0 */3 * * *",
    on_success_callback = on_success_callback,
    on_failure_callback = on_failure_callback,
    catchup=False
)

fetch_task = PythonOperator(
    task_id="fetch_active_listings",
    python_callable=fetch_active_listings,
    retries=0, 
    execution_timeout=timedelta(minutes=1),  
    dag=dag,
)

retrain_task = PythonOperator(
    task_id="call_pipeline",
    python_callable=housing_data_pipeline,
    execution_timeout=timedelta(minutes=5),  
    dag=dag,
)

upload_to_database = PythonOperator(
    task_id="upload_to_database",
    python_callable=confirmation,
    dag=dag,
)

fetch_task >> retrain_task >> upload_to_database
