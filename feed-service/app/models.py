from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FollowResponse(BaseModel):
    message: str
    follower_id: int
    following_id: int


class FeedItem(BaseModel):
    review_id: int
    user_id: int
    item_id: str
    text: str
    rating: int
    created_at: str


class HealthResponse(BaseModel):
    status: str
    service: str
    dependencies: dict[str, str] = {}
