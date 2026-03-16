"""
Hello World DAG: загрузка из БД -> обработка -> запись в БД.
Логи видны в Airflow UI (вкладка Logs у каждого task).
"""
import json
import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Логирование попадает в UI Airflow
log = logging.getLogger(__name__)

# Подключение к БД фильмов (host=db, database=movies)
# В docker-compose задаётся AIRFLOW_CONN_POSTGRES_MOVIES=postgresql://movies:movies@db:5432/movies
CONN_MOVIES = "postgres_movies"


def fetch_from_db(**context):
    """Забрать данные из БД: число фильмов и рейтингов."""
    log.info("Fetching from DB (movies)...")
    hook = PostgresHook(postgres_conn_id=CONN_MOVIES)
    conn = hook.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT (SELECT COUNT(*) FROM movies) AS movies_count, (SELECT COUNT(*) FROM ratings) AS ratings_count")
    row = cur.fetchone()
    cur.close()
    conn.close()
    movies_count = row[0] or 0
    ratings_count = row[1] or 0
    result = {"movies_count": movies_count, "ratings_count": ratings_count}
    log.info("Fetched: %s", result)
    return result


def process_data(**context):
    """Обработать: агрегат и лог."""
    ti = context["ti"]
    data = ti.xcom_pull(task_ids="fetch_from_db")
    if not data:
        data = {"movies_count": 0, "ratings_count": 0}
    total = data["movies_count"] + data["ratings_count"]
    result = {**data, "total_records": total, "message": "Hello World from DAG"}
    log.info("Processed: %s", result)
    return result


def write_to_db(**context):
    """Записать результат в таблицу dag_processing_results."""
    ti = context["ti"]
    run_id = context["run_id"]
    data = ti.xcom_pull(task_ids="process_data")
    if not data:
        data = {}
    log.info("Writing to DB: run_id=%s data=%s", run_id, data)
    hook = PostgresHook(postgres_conn_id=CONN_MOVIES)
    conn = hook.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO dag_processing_results (run_id, task_name, result_json) VALUES (%s, %s, %s)",
        (run_id, "hello_world_db", json.dumps(data)),
    )
    conn.commit()
    cur.close()
    conn.close()
    log.info("Written to dag_processing_results successfully.")
    return data


with DAG(
    dag_id="hello_world_db_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["hello", "db"],
) as dag:
    fetch = PythonOperator(
        task_id="fetch_from_db",
        python_callable=fetch_from_db,
    )
    process = PythonOperator(
        task_id="process_data",
        python_callable=process_data,
    )
    write = PythonOperator(
        task_id="write_to_db",
        python_callable=write_to_db,
    )
    fetch >> process >> write
