from typing import List

from fastapi import APIRouter

from app.models import ReviewCreate, ReviewResponse, HealthResponse
from app.service import (
    create_review_service,
    get_reviews_by_item_service,
    get_reviews_by_user_service,
    get_all_reviews_service
)


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "reviews-service"
    }


@router.post("/reviews", response_model=ReviewResponse)
def create_review(payload: ReviewCreate):
    return create_review_service(payload.model_dump())


@router.get("/reviews", response_model=List[ReviewResponse])
def get_reviews():
    return get_all_reviews_service()


@router.get("/reviews/item/{item_id}", response_model=List[ReviewResponse])
def get_reviews_by_item(item_id: str):
    return get_reviews_by_item_service(item_id)


@router.get("/reviews/user/{user_id}", response_model=List[ReviewResponse])
def get_reviews_by_user(user_id: int):
    return get_reviews_by_user_service(user_id)