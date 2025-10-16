#!/bin/bash
set -e  

echo "Starting Airflow Setup..."

export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=True

if [ ! -f /opt/airflow/airflow_initialized ]; then
    echo "Resetting Airflow DB..."
    airflow db reset -y  
    airflow db init

    echo "Creating admin user (Airflow 3.0)..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email asmaitra2006@gmail.com \
        --password admin

    touch /opt/airflow/airflow_initialized
else
    echo "Airflow DB already initialized. Skipping DB setup."
fi

airflow scheduler &

exec airflow webserver
