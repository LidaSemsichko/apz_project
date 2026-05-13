from typing import List, Optional

from fastapi import APIRouter, Header, Query

from common.auth_client import verify_authorization_header
from app.models import MovieCreate, MovieResponse, MovieUpdate
from app.service import (
    create_movie_service,
    delete_movie_service,
    get_all_movies_service,
    get_health_dependencies,
    get_movie_service,
    search_movies_service,
    update_movie_service,
)


router = APIRouter()


def require_user(authorization: str | None):
    return verify_authorization_header(authorization)


@router.get("/health")
def health():
    dependencies = get_health_dependencies()
    status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
    return {
        "status": status,
        "service": "catalog-service",
        "dependencies": dependencies,
    }


@router.post("/catalog", response_model=MovieResponse)
def create_movie(payload: MovieCreate, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return create_movie_service(payload.model_dump())


@router.get("/catalog", response_model=List[MovieResponse])
def get_catalog(authorization: str | None = Header(default=None)):
    require_user(authorization)
    return get_all_movies_service()


@router.get("/catalog/search", response_model=List[MovieResponse])
def search_catalog(
    title: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    year: Optional[int] = Query(default=None),
    authorization: str | None = Header(default=None),
):
    require_user(authorization)
    return search_movies_service(
        title=title,
        genre=genre,
        year=year,
    )


@router.get("/catalog/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return get_movie_service(movie_id)


@router.put("/catalog/{movie_id}", response_model=MovieResponse)
def update_movie(
    movie_id: str,
    payload: MovieUpdate,
    authorization: str | None = Header(default=None),
):
    require_user(authorization)
    return update_movie_service(movie_id, payload.model_dump())


@router.delete("/catalog/{movie_id}")
def delete_movie(movie_id: str, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return delete_movie_service(movie_id)
