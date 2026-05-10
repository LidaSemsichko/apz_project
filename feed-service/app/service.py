from app.repository import (
    follow_user,
    get_feed_for_user,
    get_user_reviews,
    get_recommendations
)


def follow_user_service(follower_id: int, following_id: int):
    follow_user(follower_id=follower_id, following_id=following_id)

    return {
        "message": "User followed successfully",
        "follower_id": follower_id,
        "following_id": following_id
    }


def get_feed_service(user_id: int):
    return get_feed_for_user(user_id)


def get_user_reviews_service(user_id: int):
    return get_user_reviews(user_id)


def get_recommendations_service(user_id: int):
    return get_recommendations(user_id)