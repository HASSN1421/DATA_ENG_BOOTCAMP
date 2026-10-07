import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="hello_pipeline",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    tags=["learning"],
) as dag:

    run_python_script = BashOperator(
        task_id="run_python_script",
        bash_command="python /opt/airflow/scripts/hello.py",
    )