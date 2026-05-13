from common.errors import NotFoundError
from app.repository import (
    create_movie,
    delete_movie,
    get_all_movies,
    get_database_health,
    get_movie_by_id,
    search_movies,
    to_response,
    update_movie,
)


def create_movie_service(movie_data: dict):
    movie = create_movie(movie_data)
    return to_response(movie)


def get_all_movies_service():
    movies = get_all_movies()
    return [to_response(movie) for movie in movies]


def get_movie_service(movie_id: str):
    movie = get_movie_by_id(movie_id)

    if not movie:
        raise NotFoundError("Movie not found")

    return to_response(movie)


def search_movies_service(title=None, genre=None, year=None):
    movies = search_movies(title=title, genre=genre, year=year)
    return [to_response(movie) for movie in movies]


def update_movie_service(movie_id: str, update_data: dict):
    movie = update_movie(movie_id, update_data)

    if not movie:
        raise NotFoundError("Movie not found")

    return to_response(movie)


def delete_movie_service(movie_id: str):
    deleted = delete_movie(movie_id)

    if not deleted:
        raise NotFoundError("Movie not found")

    return {
        "message": "Movie deleted successfully",
        "movie_id": movie_id,
    }


def get_health_dependencies():
    return {
        "mongo": get_database_health(),
    }
