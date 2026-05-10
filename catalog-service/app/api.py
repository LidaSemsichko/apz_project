from typing import Optional, List

from fastapi import APIRouter, Query

from app.models import MovieCreate, MovieUpdate, MovieResponse
from app.service import (
    create_movie_service,
    get_all_movies_service,
    get_movie_service,
    search_movies_service,
    update_movie_service,
    delete_movie_service
)


router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "catalog-service"
    }


@router.post("/catalog", response_model=MovieResponse)
def create_movie(payload: MovieCreate):
    return create_movie_service(payload.model_dump())


@router.get("/catalog", response_model=List[MovieResponse])
def get_catalog():
    return get_all_movies_service()


@router.get("/catalog/search", response_model=List[MovieResponse])
def search_catalog(
    title: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    year: Optional[int] = Query(default=None)
):
    return search_movies_service(
        title=title,
        genre=genre,
        year=year
    )


@router.get("/catalog/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str):
    return get_movie_service(movie_id)


@router.put("/catalog/{movie_id}", response_model=MovieResponse)
def update_movie(movie_id: str, payload: MovieUpdate):
    return update_movie_service(movie_id, payload.model_dump())


@router.delete("/catalog/{movie_id}")
def delete_movie(movie_id: str):
    return delete_movie_service(movie_id)