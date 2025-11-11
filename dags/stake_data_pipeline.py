from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
sys.path.append("/opt/airflow/project")

from etl.airflow_dags.dag_source_stace import run_process_stake_data  # Импортируем функцию запуска процесса

# Default arguments for DAG
default_args = {
    "owner": "data_team",                  # Owner of the DAG
    "depends_on_past": False,              # Do not wait for previous DAG runs
    "email": ["alerts@example.com"],       # Optional email for alerts
    "email_on_failure": False,             # Set True to receive email on failure
    "email_on_retry": False,               # Set True to receive email on retry
    "retries": 1,                          # Number of retries on failure
    "retry_delay": timedelta(hours=1),     # Wait 1 hour before retry
}

# Define the DAG
with DAG(
    dag_id="stake_data_pipeline",          # Unique DAG ID
    default_args=default_args,
    description="Fetch, transform and send Stake.com data every 4 hours",
    schedule_interval="0 */4 * * *",       # Cron: every 4 hours at minute 0
    start_date=datetime(2025, 11, 11),     # Start date for the DAG
    catchup=False,                         # Do not run past DAG runs
    tags=["stake", "bets", "etl"],         # Tags for organization
) as dag:

    # PythonOperator to run the async Stake process
    run_stake_task = PythonOperator(
        task_id="run_stake_process",
        python_callable=run_process_stake_data,  # Synchronous wrapper function
    )

    # Task dependencies (only one task here)
    run_stake_task
