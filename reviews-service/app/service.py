import json
import os
import time
from typing import List

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from app.repository import (
    create_review,
    get_reviews_by_item,
    get_reviews_by_user,
    get_all_reviews
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "review.created")

producer = None


def get_kafka_producer():
    global producer

    if producer is not None:
        return producer

    max_attempts = 15

    for attempt in range(1, max_attempts + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda value: json.dumps(value).encode("utf-8")
            )
            print("[REVIEWS] Kafka producer connected successfully", flush=True)
            return producer

        except NoBrokersAvailable:
            print(f"[REVIEWS] Kafka not ready, attempt {attempt}/{max_attempts}", flush=True)
            time.sleep(2)

    raise RuntimeError("Kafka is not available after retries")


def review_to_response(review, event_published: bool = False) -> dict:
    return {
        "id": review.id,
        "user_id": review.user_id,
        "item_id": review.item_id,
        "text": review.text,
        "rating": review.rating,
        "created_at": review.created_at,
        "event_published": event_published
    }


def publish_review_created_event(review) -> bool:
    event = {
        "event_type": "review.created",
        "review_id": review.id,
        "user_id": review.user_id,
        "item_id": review.item_id,
        "text": review.text,
        "rating": review.rating,
        "created_at": review.created_at.isoformat()
    }

    kafka_producer = get_kafka_producer()
    kafka_producer.send(KAFKA_TOPIC, event)
    kafka_producer.flush()

    print(f"[REVIEWS] Published event to Kafka: {event}", flush=True)

    return True


def create_review_service(payload: dict):
    review = create_review(
        user_id=payload["user_id"],
        item_id=payload["item_id"],
        text=payload["text"],
        rating=payload["rating"]
    )

    event_published = publish_review_created_event(review)

    return review_to_response(review, event_published=event_published)


def get_reviews_by_item_service(item_id: str) -> List[dict]:
    reviews = get_reviews_by_item(item_id)
    return [review_to_response(review) for review in reviews]


def get_reviews_by_user_service(user_id: int) -> List[dict]:
    reviews = get_reviews_by_user(user_id)
    return [review_to_response(review) for review in reviews]


def get_all_reviews_service() -> List[dict]:
    reviews = get_all_reviews()
    return [review_to_response(review) for review in reviews]