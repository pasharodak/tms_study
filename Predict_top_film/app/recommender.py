"""
Runtime recommender: loads trained artifacts and serves recommendations.
"""

import json
import pickle
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib

from .config import ARTIFACTS_PATH, RATINGS_FILE


class Recommender:
    def __init__(self) -> None:
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        artifacts_dir = ARTIFACTS_PATH

        self.model = joblib.load(artifacts_dir / "classifier.joblib")
        self.svd = joblib.load(artifacts_dir / "svd.joblib")

        self.X_item = np.load(artifacts_dir / "X_item.npy")

        with open(artifacts_dir / "user_embeddings.pkl", "rb") as f:
            self.user_embeddings: Dict[int, np.ndarray] = pickle.load(f)

        with open(artifacts_dir / "movie_id_to_idx.json", "r", encoding="utf-8") as f:
            self.movie_id_to_idx = {int(k): int(v) for k, v in json.load(f).items()}

        self.movies = pd.read_parquet(artifacts_dir / "movies.parquet")
        self.ratings = pd.read_csv(RATINGS_FILE)

    def recommend_for_user(
        self,
        user_id: int,
        top_n: int = 10,
        alpha: float = 0.7,
        beta: float = 0.3,
    ) -> Optional[pd.DataFrame]:
        if user_id not in self.user_embeddings:
            return None

        user_vec = self.user_embeddings[user_id].reshape(1, -1)
        user_block = np.repeat(user_vec, self.X_item.shape[0], axis=0)

        X_pred = np.hstack([user_block, self.X_item])

        clf_score = self.model.predict_proba(X_pred)[:, 1]
        emb_score = cosine_similarity(user_vec, self.X_item)[0]

        # popularity penalty as in notebook
        pop = self.movies["popularity"].values
        pop_penalty = 1 / (1 + np.log1p(pop))

        final_score = (alpha * clf_score + beta * emb_score) * pop_penalty

        seen = self.ratings[self.ratings["userId"] == user_id]["movieId"].values

        recs = self.movies.copy()
        recs["score"] = final_score
        recs = recs[~recs["id"].isin(seen)]

        recs = recs.sort_values("score", ascending=False).head(top_n)
        return recs[["id", "title", "genres_list", "score"]]

    def recommend_by_movies(
        self,
        movie_ids: List[int],
        top_n: int = 10,
        alpha: float = 0.7,
        beta: float = 0.3,
    ) -> Optional[pd.DataFrame]:
        """Recommend top_n movies based on a list of liked movie IDs (TMDB)."""
        if not movie_ids:
            return None
        # Resolve to indices and build preference vector (mean of item embeddings)
        indices = []
        for mid in movie_ids:
            if mid in self.movie_id_to_idx:
                indices.append(self.movie_id_to_idx[mid])
        if not indices:
            return None
        indices = np.array(indices)
        pref_vec = np.mean(self.X_item[indices], axis=0).reshape(1, -1)
        # Score all items
        user_block = np.repeat(pref_vec, self.X_item.shape[0], axis=0)
        X_pred = np.hstack([user_block, self.X_item])
        clf_score = self.model.predict_proba(X_pred)[:, 1]
        emb_score = cosine_similarity(pref_vec, self.X_item)[0]
        pop = self.movies["popularity"].values
        pop_penalty = 1 / (1 + np.log1p(pop))
        final_score = (alpha * clf_score + beta * emb_score) * pop_penalty
        recs = self.movies.copy()
        recs["score"] = final_score
        recs = recs[~recs["id"].isin(movie_ids)]
        recs = recs.sort_values("score", ascending=False).head(top_n)
        return recs[["id", "title", "genres_list", "score"]]


recommender_instance: Optional[Recommender] = None


def get_recommender() -> Recommender:
    global recommender_instance
    if recommender_instance is None:
        recommender_instance = Recommender()
    return recommender_instance

