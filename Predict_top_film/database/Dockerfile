# Database population container: schema is applied by postgres init;
# this image only runs the ingest script against the db service.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py ingest.py .

# Ingest runs with DATA_PATH mounted (e.g. ./dataset -> /data)
ENV DATA_PATH=/data
ENV PYTHONPATH=/app

CMD ["python", "ingest.py"]
