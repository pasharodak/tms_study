# Database (separate container and folder)

This folder holds everything for the **database**: schema, population script, and the image for the **db_populate** container.

## Contents

| File | Purpose |
|------|--------|
| `init.sql` | Schema (movies, ratings). Run automatically when the Postgres container starts. |
| `db.py` | SQLAlchemy models and engine; used by `ingest.py`. |
| `ingest.py` | Loads CSVs from `DATA_PATH` into the DB. Used by the db_populate container. |
| `requirements.txt` | Python deps for ingest (pandas, sqlalchemy, psycopg2). |
| `Dockerfile` | Image for the **db_populate** container (runs ingest only). |

## Containers

- **db** (Postgres): Uses `init.sql` from this folder. No Python or app code.
- **db_populate**: Builds from this folder; runs `ingest.py` once with `./dataset` mounted at `/data`, then exits. Run manually after `db` is up:

  ```bash
  docker-compose run --rm db_populate
  ```

## Env (for db_populate)

- `DATABASE_URL` – e.g. `postgresql://movies:movies@db:5432/movies`
- `DATA_PATH` – directory containing `movies_metadata.csv`, `ratings_small.csv`, `links_small.csv` (default `/data` in container)
