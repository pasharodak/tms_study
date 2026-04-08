"""
Training pipeline for the recommendation model.

Usage (inside container, after mounting dataset and artifacts paths):
    python -m app.model_pipeline
"""

from pathlib import Path
import json
import pickle

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
import joblib

from .config import MOVIES_METADATA_FILE, RATINGS_FILE, LINKS_FILE, ARTIFACTS_PATH


np.random.seed(42)


def parse_genres(x: str):
    try:
        return [g["name"] for g in eval(x)]
    except Exception:
        return []


def train() -> None:
    print("Loading data...")
    movies = pd.read_csv(MOVIES_METADATA_FILE, low_memory=False)
    ratings = pd.read_csv(RATINGS_FILE)

    # keep only numeric ids
    movies = movies[movies["id"].astype(str).str.isnumeric()].copy()
    movies["id"] = movies["id"].astype(int)

    # drop duplicate movie ids
    movies = movies.drop_duplicates(subset="id").reset_index(drop=True)

    # map MovieLens movieId -> TMDB id via links, then filter to known movies
    links = pd.read_csv(LINKS_FILE).dropna(subset=["tmdbId"])
    links["tmdbId"] = links["tmdbId"].astype(int)
    ratings = ratings.merge(links[["movieId", "tmdbId"]], on="movieId", how="inner")
    ratings = ratings[ratings["tmdbId"].isin(movies["id"])]
    ratings = ratings.rename(columns={"tmdbId": "movie_id"}).drop(columns=["movieId"])

    print(f"Movies: {len(movies)}, ratings: {len(ratings)}")

    # movie features
    movies["genres_list"] = movies["genres"].fillna("[]").apply(parse_genres)
    movies["overview"] = movies["overview"].fillna("")
    movies["tagline"] = movies["tagline"].fillna("")
    movies["text"] = movies["overview"] + " " + movies["tagline"]

    print("Building text features...")
    tfidf = TfidfVectorizer(
        max_features=5000,
        stop_words="english",
        ngram_range=(1, 2),
    )
    X_text = tfidf.fit_transform(movies["text"])

    print("Building genre features...")
    mlb = MultiLabelBinarizer()
    X_genres = csr_matrix(mlb.fit_transform(movies["genres_list"]))

    print("Building numeric features...")
    num_cols = ["popularity", "runtime", "vote_average", "vote_count"]
    movies[num_cols] = movies[num_cols].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0)
    scaler = StandardScaler()
    X_num = csr_matrix(scaler.fit_transform(movies[num_cols]))

    print("Stacking features...")
    X_item_raw = hstack([X_text, X_genres, X_num])
    print("Raw item features:", X_item_raw.shape)

    print("Computing item embeddings (SVD)...")
    svd = TruncatedSVD(n_components=128, random_state=42)
    X_item = svd.fit_transform(X_item_raw)
    print("Item embeddings:", X_item.shape)

    movie_id_to_idx = dict(zip(movies["id"], range(len(movies))))

    # ratings with indices (movie_id = TMDB id)
    ratings = ratings.copy()
    ratings["movie_idx"] = ratings["movie_id"].map(movie_id_to_idx)
    ratings = ratings.dropna(subset=["movie_idx"])
    ratings["movie_idx"] = ratings["movie_idx"].astype(int)

    # user embeddings
    print("Computing user embeddings...")
    user_embeddings = {}
    for user_id, grp in ratings.groupby("userId"):
        idxs = grp["movie_idx"].values
        weights = grp["rating"].values
        user_embeddings[int(user_id)] = np.average(
            X_item[idxs], axis=0, weights=weights
        )

    print("Users with embeddings:", len(user_embeddings))

    # train classifier
    print("Training classifier...")
    model = SGDClassifier(loss="log_loss", max_iter=1, learning_rate="optimal")

    batch_size = 50000
    ratings_list = list(ratings.itertuples(index=False))
    n_batches = int(np.ceil(len(ratings_list) / batch_size))

    for epoch in range(5):
        for i in range(n_batches):
            batch = ratings_list[i * batch_size : (i + 1) * batch_size]

            X_batch, y_batch = [], []
            for row in batch:
                u, m = row.userId, row.movie_idx
                if u not in user_embeddings:
                    continue

                X_batch.append(
                    np.hstack([user_embeddings[u], X_item[m]])
                )
                y_batch.append(1 if row.rating >= 4.0 else 0)

            if not X_batch:
                continue

            X_batch = np.array(X_batch, dtype=np.float32)
            y_batch = np.array(y_batch)

            if epoch == 0 and i == 0:
                model.partial_fit(X_batch, y_batch, classes=[0, 1])
            else:
                model.partial_fit(X_batch, y_batch)

        print(f"Epoch {epoch + 1} finished")

    # save artifacts
    ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)
    print(f"Saving artifacts to {ARTIFACTS_PATH} ...")

    joblib.dump(tfidf, ARTIFACTS_PATH / "tfidf.joblib")
    joblib.dump(mlb, ARTIFACTS_PATH / "mlb_genres.joblib")
    joblib.dump(scaler, ARTIFACTS_PATH / "scaler.joblib")
    joblib.dump(svd, ARTIFACTS_PATH / "svd.joblib")
    joblib.dump(model, ARTIFACTS_PATH / "classifier.joblib")

    np.save(ARTIFACTS_PATH / "X_item.npy", X_item)

    with open(ARTIFACTS_PATH / "user_embeddings.pkl", "wb") as f:
        pickle.dump(user_embeddings, f)

    with open(ARTIFACTS_PATH / "movie_id_to_idx.json", "w", encoding="utf-8") as f:
        json.dump({int(k): int(v) for k, v in movie_id_to_idx.items()}, f)

    # store movies metadata for serving
    movies_meta_path: Path = ARTIFACTS_PATH / "movies.parquet"
    movies[["id", "title", "genres_list", "popularity"]].to_parquet(
        movies_meta_path, index=False
    )

    print("Training pipeline completed.")


if __name__ == "__main__":
    train()

