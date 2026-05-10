import os
import time
from typing import Optional, List
from uuid import uuid4

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/catalog_db?replicaSet=rs0"
)

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client["catalog_db"]
movies_collection = db["movies"]


def wait_for_mongo():
    max_attempts = 15

    for attempt in range(1, max_attempts + 1):
        try:
            client.admin.command("ping")
            print("[CATALOG] MongoDB connected successfully")
            return
        except ServerSelectionTimeoutError:
            print(f"[CATALOG] MongoDB not ready, attempt {attempt}/{max_attempts}")
            time.sleep(2)

    raise RuntimeError("MongoDB is not available after retries")


def create_movie(movie_data: dict) -> dict:
    movie_id = str(uuid4())

    document = {
        "_id": movie_id,
        **movie_data
    }

    movies_collection.insert_one(document)
    return document


def get_all_movies() -> List[dict]:
    return list(movies_collection.find())


def get_movie_by_id(movie_id: str) -> Optional[dict]:
    return movies_collection.find_one({"_id": movie_id})


def search_movies(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None
) -> List[dict]:
    query = {}

    if title:
        query["title"] = {"$regex": title, "$options": "i"}

    if genre:
        query["genres"] = {"$in": [genre]}

    if year:
        query["year"] = year

    return list(movies_collection.find(query))


def update_movie(movie_id: str, update_data: dict) -> Optional[dict]:
    clean_data = {
        key: value
        for key, value in update_data.items()
        if value is not None
    }

    if not clean_data:
        return get_movie_by_id(movie_id)

    movies_collection.update_one(
        {"_id": movie_id},
        {"$set": clean_data}
    )

    return get_movie_by_id(movie_id)


def delete_movie(movie_id: str) -> bool:
    result = movies_collection.delete_one({"_id": movie_id})
    return result.deleted_count == 1


def to_response(document: dict) -> dict:
    return {
        "id": document["_id"],
        "title": document["title"],
        "description": document["description"],
        "genres": document.get("genres", []),
        "year": document["year"],
        "director": document["director"],
        "poster_url": document.get("poster_url")
    }