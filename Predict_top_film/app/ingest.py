"""
Ingest data from CSV files in `dataset/` into PostgreSQL.

This is a one-off (or occasional) job:
    python -m app.ingest
"""

import pandas as pd

from .config import MOVIES_METADATA_FILE, RATINGS_FILE, LINKS_FILE
from .db import Movie, Rating, SessionLocal, init_db


def load_movies(session):
    """Load movies from metadata CSV. Returns set of inserted movie ids."""
    df = pd.read_csv(MOVIES_METADATA_FILE, low_memory=False)

    # keep only numeric ids as in the notebook
    df = df[df["id"].astype(str).str.isnumeric()].copy()
    df["id"] = df["id"].astype(int)

    # select only columns we care about
    cols = [
        "id",
        "title",
        "overview",
        "tagline",
        "genres",
        "popularity",
        "runtime",
        "vote_average",
        "vote_count",
        "release_date",
    ]
    df = df[cols]

    # fill NaNs to avoid issues
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
            popularity=float(row.popularity)
            if pd.notna(row.popularity)
            else 0.0,
            runtime=float(row.runtime) if pd.notna(row.runtime) else 0.0,
            vote_average=float(row.vote_average)
            if pd.notna(row.vote_average)
            else 0.0,
            vote_count=int(row.vote_count) if pd.notna(row.vote_count) else 0,
            release_date=str(row.release_date) if pd.notna(row.release_date) else "",
        )
        for row in df.itertuples(index=False)
    ]

    session.bulk_save_objects(objects)
    return set(df["id"].astype(int).tolist())


def load_ratings(session, valid_movie_ids: set) -> None:
    """Load ratings; map MovieLens movieId to TMDB id via links."""
    ratings = pd.read_csv(RATINGS_FILE)
    links = pd.read_csv(LINKS_FILE)
    # drop rows where tmdbId is missing
    links = links.dropna(subset=["tmdbId"])
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


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        # Clear existing data for idempotent re-run
        session.query(Rating).delete()
        session.query(Movie).delete()
        session.commit()
        movie_ids = load_movies(session)
        load_ratings(session, movie_ids)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

