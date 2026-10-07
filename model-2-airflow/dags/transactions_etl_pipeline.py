from datetime import timedelta

import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


with DAG(
    dag_id="transactions_etl_pipeline",
    start_date=pendulum.datetime(
        2026,
        1,
        1,
        tz="UTC"
    ),
    schedule="0 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["etl", "data-warehouse", "learning"],
) as dag:


    extract_transactions = BashOperator(
        task_id="extract_transactions",
        bash_command="""
        python /opt/airflow/scripts/extract_transactions.py
        """,
    )


    extract_excel = BashOperator(
        task_id="extract_excel",
        bash_command="""
        python /opt/airflow/scripts/extract_excel.py
        """,
    )


    quality_check = BashOperator(
        task_id="check_staging_quality",
        bash_command="""
        python /opt/airflow/scripts/check_staging_quality.py
        """,
    )


    clean_reference_data = BashOperator(
        task_id="clean_reference_data",
        bash_command="""
        python /opt/airflow/scripts/clean_reference_data.py
        """,
    )


    clean_transactions = BashOperator(
        task_id="clean_transactions",
        bash_command="""
        python /opt/airflow/scripts/clean_transactions.py
        """,
    )


    load_dimensions = BashOperator(
        task_id="load_dimensions",
        bash_command="""
        python /opt/airflow/scripts/load_dimensions.py
        """,
    )


    load_fact = BashOperator(
        task_id="load_fact",
        bash_command="""
        python /opt/airflow/scripts/load_fact.py
        """,
    )


    final_validation = BashOperator(
        task_id="final_validation",
        bash_command="""
        python /opt/airflow/scripts/final_validation.py
        """,
    )


    [
        extract_transactions,
        extract_excel
    ] >> quality_check


    quality_check \
        >> clean_reference_data \
        >> clean_transactions \
        >> load_dimensions \
        >> load_fact \
        >> final_validation