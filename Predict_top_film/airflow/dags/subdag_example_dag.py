"""
Пример SubDAG (для учебных целей).

Главный DAG: subdag_parent_dag
- таск start
- SubDagOperator, который запускает под-DAG subdag_parent_dag.sub_workflow
- таск end

SubDAG: subdag_parent_dag.sub_workflow
- task a
- task b

В UI Airflow SubDAG отображается как один task (sub_workflow),
но внутри него можно "провалиться" и увидеть отдельный граф.

Важно: SubDAG в современных версиях Airflow считается антипаттерном.
В боевом коде лучше использовать TaskGroup, как в predict_recommend_dag.
"""

from datetime import datetime

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.subdag import SubDagOperator
from airflow.operators.python import PythonOperator


def _print_msg(msg: str):
    print(msg)


def subdag(parent_dag_id: str, subdag_dag_id: str, start_date: datetime) -> DAG:
    """
    Фабрика SubDAG'а.

    parent_dag_id: id родительского DAG (например, "subdag_parent_dag")
    subdag_dag_id: id subdag внутри родителя (например, "sub_workflow")

    Итоговый dag_id SubDAG'а в Airflow = "parent_dag_id.subdag_dag_id".
    """
    dag_id = f"{parent_dag_id}.{subdag_dag_id}"
    dag = DAG(
        dag_id=dag_id,
        start_date=start_date,
        schedule_interval=None,
        catchup=False,
        tags=["subdag", "example"],
    )

    with dag:
        a = PythonOperator(
            task_id="task_a",
            python_callable=_print_msg,
            op_args=["SubDAG task A"],
        )
        b = PythonOperator(
            task_id="task_b",
            python_callable=_print_msg,
            op_args=["SubDAG task B"],
        )

        a >> b

    return dag


PARENT_DAG_ID = "subdag_parent_dag"
SUBDAG_ID = "sub_workflow"

with DAG(
    dag_id=PARENT_DAG_ID,
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["subdag", "example"],
) as parent_dag:
    start = DummyOperator(task_id="start")

    sub_workflow = SubDagOperator(
        task_id=SUBDAG_ID,
        subdag=subdag(PARENT_DAG_ID, SUBDAG_ID, start_date=parent_dag.start_date),
    )

    end = DummyOperator(task_id="end")

    start >> sub_workflow >> end

