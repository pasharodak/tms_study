# Top Films by Client Preferences

Recommendation service: send a list of movies you like and get top 10 recommendations.

## Project layout

- **`database/`** – Database schema, population script, and **separate container** for DB startup/population. No app code here.
- **`app/`** – FastAPI app and model (recommendations). Connects to the DB container.

## Docker setup (separate containers)

The database, its population, and startup live in a **separate container and folder** (`database/`). Three containers:

| Container | Service | Folder / Build | Role |
|-----------|---------|----------------|------|
| `movies_db` | `db` | `database/init.sql` (mounted) | PostgreSQL only; runs schema on first start |
| `movies_db_populate` | `db_populate` | build from `database/` | Runs ingest (CSV → DB) once, then exits |
| `movies_app` | `app` | build from project root | FastAPI only; connects to `db` |

- **Database container (`db`)**  
  Postgres 16. Schema from `database/init.sql` runs automatically on first start. Data is stored in the **named volume** `db_data`.

- **Database population container (`db_populate`)**  
  Built from `database/Dockerfile`. Runs `database/ingest.py` with `./dataset` mounted; populates the DB and exits. Run once after `db` is up: `docker-compose run --rm db_populate`.

- **App container (`app`)**  
  FastAPI app. Connects to the DB with `DATABASE_URL=...@db:5432/movies` over the `app_net` network. Waits for `db` to be healthy before starting.

## Quick start (Docker)

From the project root (`Predict_top_film/`):

### 1. Start DB and app

```bash
docker-compose up -d --build
```

### 2. Populate the database (separate container)

```bash
docker-compose run --rm db_populate
```

Uses the **database** container image (from `database/`). Loads `dataset/movies_metadata.csv`, `dataset/ratings_small.csv`, and `dataset/links_small.csv` into PostgreSQL.

### 3. Train the model

```bash
docker-compose run --rm app python -m app.model_pipeline
```

Writes artifacts to `model_artifacts/` (mounted volume).

### 4. Request recommendations

Send a JSON body with **movie IDs** (TMDB ids from the catalog) and optional `top_n` (default 10):

```bash
curl -X POST http://localhost:8000/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"movie_ids\": [862, 8844, 31357], \"top_n\": 10}"
```

Example IDs: `862` (Toy Story), `8844` (Jumanji), `31357` (Waiting to Exhale). Response: list of recommended movies with `movie_id`, `title`, `genres`, `score`.

---

## Run everything (first time)

From the project root, run the script to start containers, populate the DB, train the model, and print the recommend command:

```powershell
.\run.ps1
```

Then request recommendations (PowerShell):

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/recommend" -ContentType "application/json" -Body '{"movie_ids":[862,8844,31357],"top_n":10}'
```

---

## Reference

- **Health:** `GET http://localhost:8000/health`
- **List sample movies (get movie_ids for recommend):** `GET http://localhost:8000/movies?limit=20`
- **API docs:** `http://localhost:8000/docs`
