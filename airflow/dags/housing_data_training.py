from airflow.decorators import dag, task
from pendulum import datetime, duration
import requests
import pandas as pd
import sys
import os
import numpy as np
from pathlib import Path
from prometheus_client import CollectorRegistry, Counter, Summary, push_to_gateway

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = __file__.decode('utf-8') if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.append(MODEL_PATH)

import core.fetch_housing_data as fetch_housing_data
import pipeline
import core.insert_into_postgredb as insert_into_postgredb

os.environ['NO_PROXY'] = '*'

# Dedicated registry so importing multiple DAG files does not duplicate metric names.
_PROM_REGISTRY = CollectorRegistry()
DAG_SUCCESS = Counter(
    "dag_success_total", "Total successful DAG runs", ["dag_id"], registry=_PROM_REGISTRY
)
DAG_FAILURE = Counter(
    "dag_failure_total", "Total failed DAG runs", ["dag_id"], registry=_PROM_REGISTRY
)
DAG_DURATION = Summary(
    "dag_duration_seconds", "DAG execution duration in seconds", ["dag_id"], registry=_PROM_REGISTRY
)
# Optional; if unset or gateway down, callbacks still succeed (metrics are best-effort).
PUSHGATEWAY_URL = os.environ.get("AIRFLOW_PROMETHEUS_PUSHGATEWAY", "http://localhost:9091")


def _push_metrics(job: str) -> None:
    if not PUSHGATEWAY_URL:
        return
    try:
        push_to_gateway(PUSHGATEWAY_URL, job=job, registry=_PROM_REGISTRY)
    except OSError:
        pass


def on_success_callback(context):
    dag_id = context["dag"].dag_id
    DAG_SUCCESS.labels(dag_id=dag_id).inc()
    duration = context["dag_run"].end_date - context["dag_run"].start_date
    DAG_DURATION.labels(dag_id=dag_id).observe(duration.total_seconds())
    _push_metrics(dag_id)


def on_failure_callback(context):
    dag_id = context["dag"].dag_id
    DAG_FAILURE.labels(dag_id=dag_id).inc()
    _push_metrics(dag_id)


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
        # API fetch + file I/O can exceed 1m; short timeouts often kill the worker with an empty task log.
        execution_timeout=duration(minutes=30),
    )
    def fetch_active_listings():
        fetch_housing_data.fetch_active_listings()
        # Data is saved to DATA_PATH; do not return DataFrame (XCom can't serialize it)

    @task(
        execution_timeout=duration(minutes=15)
    )
    def call_pipeline(**context):
        return pipeline.housing_data_pipeline()

    @task
    def upload_to_database(**context):
        return insert_into_postgredb.confirmation()

    fetch_result = fetch_active_listings()
    pipeline_result = call_pipeline()
    upload_result = upload_to_database()
    
    fetch_result >> pipeline_result >> upload_result


# Instantiate the DAG
retrain_rental_model()
