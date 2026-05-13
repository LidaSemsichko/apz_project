from typing import List

from fastapi import APIRouter, Header

from common.auth_client import verify_authorization_header
from common.service_discovery import check_service_registered
from app.models import FeedItem, FollowResponse, HealthResponse
from app.service import (
    follow_user_service,
    get_feed_service,
    get_health_dependencies,
    get_recommendations_service,
    get_user_reviews_service,
)


router = APIRouter()


def require_user(authorization: str | None):
    return verify_authorization_header(authorization)


@router.get("/health", response_model=HealthResponse)
def health():
    dependencies = get_health_dependencies()
    dependencies["auth-service"] = check_service_registered("auth-service")
    status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
    return {
        "status": status,
        "service": "feed-api",
        "dependencies": dependencies,
    }


@router.post("/follow/{following_id}", response_model=FollowResponse)
def follow_user(
    following_id: int,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    return follow_user_service(
        follower_id=user["user_id"],
        following_id=following_id,
    )


@router.get("/feed", response_model=List[FeedItem])
def get_feed(
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    return get_feed_service(user["user_id"])


@router.get("/users/{user_id}/reviews", response_model=List[FeedItem])
def get_user_reviews(user_id: int, authorization: str | None = Header(default=None)):
    require_user(authorization)
    return get_user_reviews_service(user_id)


@router.get("/recommendations")
def get_recommendations(
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    return get_recommendations_service(user["user_id"])
