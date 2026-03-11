"""Database models and engine for the database container (ingest only)."""
import os
from sqlalchemy import Column, Integer, Float, String, Text, BigInteger, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://movies:movies@localhost:5432/movies",
)

Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    overview = Column(Text, nullable=True)
    tagline = Column(Text, nullable=True)
    genres = Column(Text, nullable=True)
    popularity = Column(Float, nullable=True)
    runtime = Column(Float, nullable=True)
    vote_average = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    release_date = Column(String, nullable=True)


class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    movie_id = Column(Integer, index=True, nullable=False)
    rating = Column(Float, nullable=False)
    timestamp = Column(BigInteger, nullable=True)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
