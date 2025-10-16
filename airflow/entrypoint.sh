#!/bin/bash
set -e  

echo "Starting Airflow Setup..."

export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=True

if [ ! -f "${AIRFLOW_HOME}/airflow_initialized" ]; then
    echo "Initializing Airflow DB..."
    airflow db reset -y
    airflow db init

    echo "Creating admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin

    touch "${AIRFLOW_HOME}/airflow_initialized"
else
    echo "Airflow already initialized. Skipping setup."
fi

echo "Starting scheduler..."
airflow scheduler &

echo "Starting webserver..."
exec airflow webserver
