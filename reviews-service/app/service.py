from typing import List

from app.repository import (
    create_review_with_outbox,
    get_all_reviews,
    get_database_health,
    get_reviews_by_item,
    get_reviews_by_user,
)


def review_to_response(review) -> dict:
    return {
        "id": review.id,
        "user_id": review.user_id,
        "item_id": review.item_id,
        "text": review.text,
        "rating": review.rating,
        "created_at": review.created_at,
    }


def create_review_service(payload: dict, current_user_id: int):
    review = create_review_with_outbox(
        user_id=current_user_id,
        item_id=payload["item_id"],
        text=payload["text"],
        rating=payload["rating"],
    )

    return review_to_response(review)


def get_reviews_by_item_service(item_id: str) -> List[dict]:
    reviews = get_reviews_by_item(item_id)
    return [review_to_response(review) for review in reviews]


def get_reviews_by_user_service(user_id: int) -> List[dict]:
    reviews = get_reviews_by_user(user_id)
    return [review_to_response(review) for review in reviews]


def get_all_reviews_service() -> List[dict]:
    reviews = get_all_reviews()
    return [review_to_response(review) for review in reviews]


def get_health_dependencies():
    return {
        "postgres": get_database_health(),
    }
