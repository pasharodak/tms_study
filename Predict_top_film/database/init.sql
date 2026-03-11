-- Initial schema for movie recommendation database
-- Runs automatically when the Postgres container starts (docker-entrypoint-initdb.d)

CREATE TABLE IF NOT EXISTS movies (
    id           INTEGER PRIMARY KEY,
    title        TEXT NOT NULL,
    overview     TEXT,
    tagline      TEXT,
    genres       TEXT,
    popularity   DOUBLE PRECISION,
    runtime      DOUBLE PRECISION,
    vote_average DOUBLE PRECISION,
    vote_count   INTEGER,
    release_date TEXT
);

CREATE TABLE IF NOT EXISTS ratings (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER NOT NULL,
    movie_id  INTEGER NOT NULL REFERENCES movies(id),
    rating    DOUBLE PRECISION NOT NULL,
    timestamp BIGINT
);
