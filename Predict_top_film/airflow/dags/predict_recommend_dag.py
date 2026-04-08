"""
DAG для предикта рекомендаций:
- берём 4 фильма (по умолчанию, можно переопределить в конфиге запуска),
- вызываем сервис рекомендаций FastAPI,
- сохраняем результат в таблицу predict_results в БД movies.
Все логи видны в Airflow UI (Logs у task'a).
"""

import json
import logging
from datetime import datetime
from typing import List

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup

log = logging.getLogger(__name__)

# Подключение к БД фильмов (как в hello_world_db_dag)
CONN_MOVIES = "postgres_movies"

# Хост приложения внутри docker-compose сети (service name `app`)
RECOMMEND_URL = "http://app:8000/recommend"

# Значения по умолчанию: 4 фильма (TMDB ids)
DEFAULT_MOVIE_IDS: List[int] = [862, 8844, 31357, 19475]
DEFAULT_TOP_N = 10


def get_input_params(**context):
    """
    TaskGroup: input.
    Берём параметры из конфигурации DAG run (4 фильма, top_n) и кладём в XCom.
    """
    dag_run = context.get("dag_run")
    conf = dag_run.conf if dag_run and dag_run.conf else {}

    movie_ids = conf.get("movie_ids", DEFAULT_MOVIE_IDS)
    top_n = int(conf.get("top_n", DEFAULT_TOP_N))

    if not isinstance(movie_ids, list) or len(movie_ids) == 0:
        raise ValueError("movie_ids must be a non-empty list of TMDB ids")

    log.info("Input params: movie_ids=%s top_n=%s", movie_ids, top_n)
    return {"movie_ids": movie_ids, "top_n": top_n}


def call_recommender(**context):
    """
    TaskGroup: call_model.
    Вызывает FastAPI сервис рекомендаций и возвращает JSON результата.
    """
    ti = context["ti"]
    params = ti.xcom_pull(task_ids="input.get_input_params")
    movie_ids = params["movie_ids"]
    top_n = params["top_n"]

    log.info("Calling recommend API for movie_ids=%s top_n=%s", movie_ids, top_n)
    resp = requests.post(
        RECOMMEND_URL,
        json={"movie_ids": movie_ids, "top_n": top_n},
        timeout=60,
    )
    try:
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover
        log.error("Error calling recommend API: %s, body=%s", exc, resp.text)
        raise

    result = resp.json()
    log.info("Recommendation result: %s", json.dumps(result, ensure_ascii=False)[:1000])
    return result


def save_result(**context):
    """
    TaskGroup: save_result.
    Берём входные параметры и результат, сохраняем строку в predict_results.
    """
    ti = context["ti"]
    run_id = context["run_id"]

    params = ti.xcom_pull(task_ids="input.get_input_params")
    result = ti.xcom_pull(task_ids="call_model.call_recommender")

    movie_ids = params["movie_ids"]
    top_n = params["top_n"]

    hook = PostgresHook(postgres_conn_id=CONN_MOVIES)
    conn = hook.get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO predict_results (run_id, input_movie_ids, top_n, result_json)
        VALUES (%s, %s, %s, %s)
        """,
        (run_id, movie_ids, top_n, json.dumps(result)),
    )
    conn.commit()
    cur.close()
    conn.close()

    log.info("Prediction saved in predict_results (run_id=%s)", run_id)
    return result


with DAG(
    dag_id="predict_recommend_dag",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["predict", "recsys"],
) as dag:
    with TaskGroup("input") as input_group:
        get_input = PythonOperator(
            task_id="get_input_params",
            python_callable=get_input_params,
        )

    with TaskGroup("call_model") as call_model_group:
        call = PythonOperator(
            task_id="call_recommender",
            python_callable=call_recommender,
        )

    with TaskGroup("save_result") as save_result_group:
        save = PythonOperator(
            task_id="save_result",
            python_callable=save_result,
        )

    # Визуально в UI: input -> call_model -> save_result
    input_group >> call_model_group >> save_result_group

