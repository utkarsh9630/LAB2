from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Define the default arguments
default_args = {
    'owner': 'Utkarsh Tripathi',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 11),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
    'email_on_retry': False,
}

# Define the DAG
with DAG(
    'dbt_commands_dag',
    default_args=default_args,
    description='DAG to run dbt commands for stock data analysis',
    schedule_interval='30 11 * * *',  # Schedule as needed
    catchup=False
) as dag:

    # Path to your dbt project (adjusted for local path in Docker)
    dbt_project_path = '/opt/airflow/dbt'  # Modify if using Docker or specific mount path

    # Task to run dbt run (compile models)
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f"/home/airflow/.local/bin/dbt run --profiles-dir {dbt_project_path} --project-dir {dbt_project_path}",
        env={
            'DBT_USER': "{{ conn.snowflake_conn.login }}",
            'DBT_PASSWORD': "{{ conn.snowflake_conn.password }}",
            'DBT_ACCOUNT': "{{ conn.snowflake_conn.extra_dejson.account }}",
            'DBT_SCHEMA': "{{ conn.snowflake_conn.schema }}",
            'DBT_DATABASE': "{{ conn.snowflake_conn.extra_dejson.database }}",
            'DBT_ROLE': "{{ conn.snowflake_conn.extra_dejson.role }}",
            'DBT_WAREHOUSE': "{{ conn.snowflake_conn.extra_dejson.warehouse }}",
            'DBT_TYPE': "snowflake"
        },
    )

    # Task to run dbt tests (test models)
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=f"/home/airflow/.local/bin/dbt test --profiles-dir {dbt_project_path} --project-dir {dbt_project_path}",
        env={
            'DBT_USER': "{{ conn.snowflake_conn.login }}",
            'DBT_PASSWORD': "{{ conn.snowflake_conn.password }}",
            'DBT_ACCOUNT': "{{ conn.snowflake_conn.extra_dejson.account }}",
            'DBT_SCHEMA': "{{ conn.snowflake_conn.schema }}",
            'DBT_DATABASE': "{{ conn.snowflake_conn.extra_dejson.database }}",
            'DBT_ROLE': "{{ conn.snowflake_conn.extra_dejson.role }}",
            'DBT_WAREHOUSE': "{{ conn.snowflake_conn.extra_dejson.warehouse }}",
            'DBT_TYPE': "snowflake"
        },
    )

    # Task to run dbt snapshot (create snapshots of data)
    dbt_snapshot = BashOperator(
        task_id='dbt_snapshot',
        bash_command=f"/home/airflow/.local/bin/dbt snapshot --profiles-dir {dbt_project_path} --project-dir {dbt_project_path}",
        env={
            'DBT_USER': "{{ conn.snowflake_conn.login }}",
            'DBT_PASSWORD': "{{ conn.snowflake_conn.password }}",
            'DBT_ACCOUNT': "{{ conn.snowflake_conn.extra_dejson.account }}",
            'DBT_SCHEMA': "{{ conn.snowflake_conn.schema }}",
            'DBT_DATABASE': "{{ conn.snowflake_conn.extra_dejson.database }}",
            'DBT_ROLE': "{{ conn.snowflake_conn.extra_dejson.role }}",
            'DBT_WAREHOUSE': "{{ conn.snowflake_conn.extra_dejson.warehouse }}",
            'DBT_TYPE': "snowflake"
        },
    )

    # Define task dependencies
    dbt_run >> dbt_test >> dbt_snapshot
