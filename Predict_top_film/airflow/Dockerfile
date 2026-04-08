FROM apache/airflow:2.10.0-python3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir apache-airflow-providers-postgres
# standalone will run db init and start webserver + scheduler
CMD ["airflow", "standalone"]
