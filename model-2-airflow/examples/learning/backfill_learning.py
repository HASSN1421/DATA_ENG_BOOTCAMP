import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="backfill_learning",
    start_date=pendulum.datetime(
        2026,
        9,
        24,
        tz="Asia/Riyadh"
    ),
    schedule="@daily",
    catchup=True,
    tags=["learning", "backfill"],
) as dag:

    show_interval = BashOperator(
        task_id="show_interval",
        bash_command="""
        echo "Logical date: {{ logical_date }}"
        echo "Start: {{ data_interval_start }}"
        echo "End: {{ data_interval_end }}"
        """
    )