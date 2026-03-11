import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://movies:movies@localhost:5432/movies",
)

DATASET_PATH: Path = Path(os.getenv("DATASET_PATH", BASE_DIR / "dataset"))
ARTIFACTS_PATH: Path = Path(os.getenv("ARTIFACTS_PATH", BASE_DIR / "model_artifacts"))

# Filenames inside DATASET_PATH
MOVIES_METADATA_FILE = DATASET_PATH / "movies_metadata.csv"
RATINGS_FILE = DATASET_PATH / "ratings_small.csv"  # lighter for experiments
LINKS_FILE = DATASET_PATH / "links_small.csv"  # MovieLens movieId -> tmdbId

ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)

