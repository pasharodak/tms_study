# Top Films by Client Preferences

Recommendation service: send a list of movies you like and get top 10 recommendations.

## Quick start (Docker)

From the project root (`Predict_top_film/`):

### 1. Start DB and app

```bash
docker-compose up -d --build
```

### 2. Populate the database

```bash
docker-compose run --rm app python -m app.ingest
```

Loads `dataset/movies_metadata.csv`, `dataset/ratings_small.csv`, and `dataset/links_small.csv` into PostgreSQL (movies + ratings with TMDB ids).

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

- **Health:** `GET http://localhost:8000/health`
- **API docs:** `http://localhost:8000/docs`
