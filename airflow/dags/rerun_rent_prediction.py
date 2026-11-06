"""
Re-run fair rent + CMA predictions from current housing_listings.

Skips scrape / geocode / travel / transit enrichment. Reads the DB, rebuilds
ML features that can be derived from stored columns, runs property-grouped OOF
XGBoost + CMA, and UPDATEs predictedrent / CMA / differenceinfairvalue.
"""
from airflow.decorators import dag, task
from pendulum import datetime, duration
import sys
import os
from pathlib import Path
from prometheus_client import CollectorRegistry, Counter, Summary, push_to_gateway

MODEL_PATH = "/opt/airflow/model"

if not os.path.exists(MODEL_PATH):
    current_file = __file__.decode("utf-8") if isinstance(__file__, bytes) else __file__
    MODEL_PATH = str(Path(current_file).resolve().parent.parent / "model")

if MODEL_PATH not in sys.path:
    sys.path.insert(0, MODEL_PATH)

import ml.rerun_rent_prediction as rerun_rent_prediction

os.environ["NO_PROXY"] = "*"

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
    dag_id="rerun_rent_prediction",
    start_date=datetime(2025, 3, 30),
    schedule=None,
    catchup=False,
    description=(
        "Recompute fair rent + CMA from current housing_listings "
        "(no scrape; UPDATE predictions only)"
    ),
    default_args={"owner": "airflow", "retries": 1, "retry_delay": duration(minutes=5)},
    on_success_callback=on_success_callback,
    on_failure_callback=on_failure_callback,
    doc_md=__doc__,
    tags=["housing", "ml", "retrain", "predictions"],
)
def rerun_rent_prediction_dag():
    @task(execution_timeout=duration(minutes=45))
    def rerun_predictions():
        return rerun_rent_prediction.rerun_rent_prediction_pipeline()

    rerun_predictions()


rerun_rent_prediction_dag()
