from typing import List

from fastapi import APIRouter, Header

from common.auth_client import verify_authorization_header
from app.models import HealthResponse, ReviewCreate, ReviewResponse
from app.service import (
    create_review_service,
    get_all_reviews_service,
    get_health_dependencies,
    get_reviews_by_item_service,
    get_reviews_by_user_service,
)


router = APIRouter()


def require_user(authorization: str | None):
    return verify_authorization_header(authorization)


@router.get("/health", response_model=HealthResponse)
def health():
    dependencies = get_health_dependencies()
    status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
    return {
        "status": status,
        "service": "reviews-service",
        "dependencies": dependencies,
    }


@router.post("/reviews", response_model=ReviewResponse)
def create_review(payload: ReviewCreate, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    return create_review_service(payload.model_dump(), current_user_id=user["user_id"])


@router.get("/reviews", response_model=List[ReviewResponse])
def get_reviews(authorization: str | None = Header(default=None)):
    require_user(authorization)
    return get_all_reviews_service()


@router.get("/reviews/item/{item_id}", response_model=List[ReviewResponse])
def get_reviews_by_item(item_id: str, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return get_reviews_by_item_service(item_id)


@router.get("/reviews/user/{user_id}", response_model=List[ReviewResponse])
def get_reviews_by_user(user_id: int, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return get_reviews_by_user_service(user_id)
