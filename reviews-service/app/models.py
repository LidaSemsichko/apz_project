from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class HealthResponse(BaseModel):
    status: str
    service: str
    dependencies: dict[str, str] = {}
