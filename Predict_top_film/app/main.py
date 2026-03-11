from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .recommender import get_recommender


class RecommendRequest(BaseModel):
    movie_ids: List[int]  # TMDB movie IDs you like
    top_n: int = 10


class Recommendation(BaseModel):
    movie_id: int
    title: str
    genres: List[str]
    score: float


class RecommendResponse(BaseModel):
    movie_ids_requested: List[int]
    items: List[Recommendation]


app = FastAPI(title="Movie Recommendation Service")


@app.get("/health")
def health() -> dict:
    # lazy-load recommender to also check artifacts presence
    try:
        _ = get_recommender()
        return {"status": "ok", "model_loaded": True}
    except Exception as exc:
        return {"status": "error", "model_loaded": False, "detail": str(exc)}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    rec = get_recommender()
    df = rec.recommend_by_movies(req.movie_ids, req.top_n)

    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail="No recommendations. Provide at least one valid TMDB movie ID from the catalog.",
        )

    items = [
        Recommendation(
            movie_id=int(row.id),
            title=row.title,
            genres=list(row.genres_list) if isinstance(row.genres_list, list) else [],
            score=float(row.score),
        )
        for row in df.itertuples(index=False)
    ]

    return RecommendResponse(movie_ids_requested=req.movie_ids, items=items)

