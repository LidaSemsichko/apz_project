import os
from typing import List, Optional
from uuid import uuid4

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from common.logging_utils import configure_logging
from common.retry import retry


MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/catalog_db?replicaSet=rs0",
)

_client = None
LOGGER = configure_logging("catalog-service")


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    return _client


def get_movies_collection():
    return get_client()["catalog_db"]["movies"]


def wait_for_mongo():
    def operation() -> None:
        get_client().admin.command("ping")

    retry(
        operation,
        attempts=15,
        delay_seconds=2,
        exceptions=(ServerSelectionTimeoutError,),
        on_retry=lambda attempt, error: LOGGER.warning(
            "event=mongo_not_ready attempt=%s max_attempts=15 error=%s",
            attempt,
            error,
        ),
    )
    LOGGER.info("event=mongo_connected")


def get_database_health() -> str:
    try:
        get_client().admin.command("ping")
        return "ok"
    except Exception:
        return "unavailable"


def create_movie(movie_data: dict) -> dict:
    movie_id = str(uuid4())
    document = {
        "_id": movie_id,
        **movie_data,
    }
    get_movies_collection().insert_one(document)
    return document


def get_all_movies() -> List[dict]:
    return list(get_movies_collection().find())


def get_movie_by_id(movie_id: str) -> Optional[dict]:
    return get_movies_collection().find_one({"_id": movie_id})


def search_movies(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
) -> List[dict]:
    query = {}

    if title:
        query["title"] = {"$regex": title, "$options": "i"}

    if genre:
        query["genres"] = {"$in": [genre]}

    if year:
        query["year"] = year

    return list(get_movies_collection().find(query))


def update_movie(movie_id: str, update_data: dict) -> Optional[dict]:
    clean_data = {
        key: value
        for key, value in update_data.items()
        if value is not None
    }

    if not clean_data:
        return get_movie_by_id(movie_id)

    get_movies_collection().update_one(
        {"_id": movie_id},
        {"$set": clean_data},
    )

    return get_movie_by_id(movie_id)


def delete_movie(movie_id: str) -> bool:
    result = get_movies_collection().delete_one({"_id": movie_id})
    return result.deleted_count == 1


def to_response(document: dict) -> dict:
    return {
        "id": document["_id"],
        "title": document["title"],
        "description": document["description"],
        "genres": document.get("genres", []),
        "year": document["year"],
        "director": document["director"],
        "poster_url": document.get("poster_url"),
    }
