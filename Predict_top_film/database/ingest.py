"""
Populate the database from CSV files.
Runs inside the database container (db_populate) or standalone with env DATABASE_URL and DATA_PATH.
"""
import os
import sys
from pathlib import Path

import pandas as pd

from db import Movie, Rating, SessionLocal, init_db

# Path to dataset CSVs; set DATA_PATH in container (e.g. /data)
DATA_PATH = Path(os.environ.get("DATA_PATH", "/data"))
MOVIES_CSV = DATA_PATH / "movies_metadata.csv"
RATINGS_CSV = DATA_PATH / "ratings_small.csv"
LINKS_CSV = DATA_PATH / "links_small.csv"


def load_movies(session):
    if not MOVIES_CSV.exists():
        raise FileNotFoundError(f"Movies CSV not found: {MOVIES_CSV}")
    df = pd.read_csv(MOVIES_CSV, low_memory=False)
    df = df[df["id"].astype(str).str.isnumeric()].copy()
    df["id"] = df["id"].astype(int)
    cols = [
        "id", "title", "overview", "tagline", "genres",
        "popularity", "runtime", "vote_average", "vote_count", "release_date",
    ]
    df = df[cols]
    df["overview"] = df["overview"].fillna("")
    df["tagline"] = df["tagline"].fillna("")
    df["genres"] = df["genres"].fillna("[]")
    objects = [
        Movie(
            id=int(row.id),
            title=row.title,
            overview=row.overview,
            tagline=row.tagline,
            genres=row.genres,
            popularity=float(row.popularity) if pd.notna(row.popularity) else 0.0,
            runtime=float(row.runtime) if pd.notna(row.runtime) else 0.0,
            vote_average=float(row.vote_average) if pd.notna(row.vote_average) else 0.0,
            vote_count=int(row.vote_count) if pd.notna(row.vote_count) else 0,
            release_date=str(row.release_date) if pd.notna(row.release_date) else "",
        )
        for row in df.itertuples(index=False)
    ]
    session.bulk_save_objects(objects)
    return set(df["id"].astype(int).tolist())


def load_ratings(session, valid_movie_ids: set):
    if not RATINGS_CSV.exists():
        raise FileNotFoundError(f"Ratings CSV not found: {RATINGS_CSV}")
    if not LINKS_CSV.exists():
        raise FileNotFoundError(f"Links CSV not found: {LINKS_CSV}")
    ratings = pd.read_csv(RATINGS_CSV)
    links = pd.read_csv(LINKS_CSV).dropna(subset=["tmdbId"])
    links["tmdbId"] = links["tmdbId"].astype(int)
    ratings = ratings.merge(links[["movieId", "tmdbId"]], on="movieId", how="inner")
    ratings = ratings[ratings["tmdbId"].isin(valid_movie_ids)]
    objects = [
        Rating(
            user_id=int(row.userId),
            movie_id=int(row.tmdbId),
            rating=float(row.rating),
            timestamp=int(row.timestamp),
        )
        for row in ratings.itertuples(index=False)
    ]
    session.bulk_save_objects(objects)


def main():
    init_db()
    session = SessionLocal()
    try:
        session.query(Rating).delete()
        session.query(Movie).delete()
        session.commit()
        movie_ids = load_movies(session)
        load_ratings(session, movie_ids)
        session.commit()
        print("Database populated successfully.", file=sys.stderr)
    except Exception as e:
        session.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
