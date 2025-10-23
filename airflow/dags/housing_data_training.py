from airflow.decorators import dag, task
from pendulum import datetime, duration
import requests
import pandas as pd
import sys
import os
import numpy as np
from pathlib import Path
from prometheus_client import Counter, Summary, push_to_gateway

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = __file__.decode('utf-8') if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import fetch_housing_data
import pipeline
import insert_into_postgredb

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


@dag(
    dag_id="retrain_rental_model",
    start_date=datetime(2025, 3, 30),
    schedule="0 12 * * *",
    catchup=False,
    description="Fetch rental listings and retrain model",
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    on_success_callback=on_success_callback,
    on_failure_callback=on_failure_callback,
    doc_md=__doc__,
    tags=["housing", "ml", "retrain"]
)
def retrain_rental_model():
    
    @task(
        retries=0,
        execution_timeout=duration(minutes=1)
    )
    def fetch_active_listings():
        return fetch_housing_data.fetch_active_listings()

    @task(
        execution_timeout=duration(minutes=5)
    )
    def call_pipeline(**context):
        return pipeline.housing_data_pipeline()

    @task
    def upload_to_database(**context):
        return insert_into_postgredb.confirmation()

    # Task dependencies
    fetch_result = fetch_active_listings()
    pipeline_result = call_pipeline()
    upload_result = upload_to_database()
    
    fetch_result >> pipeline_result >> upload_result


# Instantiate the DAG
retrain_rental_model()
