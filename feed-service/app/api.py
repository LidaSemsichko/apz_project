from typing import List

from fastapi import APIRouter, Query

from app.models import HealthResponse, FollowResponse, FeedItem
from app.service import (
    follow_user_service,
    get_feed_service,
    get_user_reviews_service,
    get_recommendations_service
)


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "feed-service"
    }


@router.post("/follow/{following_id}", response_model=FollowResponse)
def follow_user(
    following_id: int,
    follower_id: int = Query(...)
):
    return follow_user_service(
        follower_id=follower_id,
        following_id=following_id
    )


@router.get("/feed", response_model=List[FeedItem])
def get_feed(user_id: int = Query(...)):
    return get_feed_service(user_id)


@router.get("/users/{user_id}/reviews", response_model=List[FeedItem])
def get_user_reviews(user_id: int):
    return get_user_reviews_service(user_id)


@router.get("/recommendations")
def get_recommendations(user_id: int = Query(...)):
    return get_recommendations_service(user_id)