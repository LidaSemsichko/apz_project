from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    user_id: int
    item_id: str
    text: str
    rating: int = Field(ge=1, le=10)


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    item_id: str
    text: str
    rating: int
    created_at: datetime
    event_published: bool = False


class HealthResponse(BaseModel):
    status: str
    service: str