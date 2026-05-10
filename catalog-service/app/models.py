from pydantic import BaseModel, Field
from typing import List, Optional


class MovieCreate(BaseModel):
    title: str
    description: str
    genres: List[str] = Field(default_factory=list)
    year: int
    director: str
    poster_url: Optional[str] = None


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genres: Optional[List[str]] = None
    year: Optional[int] = None
    director: Optional[str] = None
    poster_url: Optional[str] = None


class MovieResponse(BaseModel):
    id: str
    title: str
    description: str
    genres: List[str]
    year: int
    director: str
    poster_url: Optional[str] = None