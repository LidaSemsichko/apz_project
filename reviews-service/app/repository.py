import json
import os
from datetime import datetime
from typing import Callable, List

from sqlalchemy import Column, DateTime, Integer, String, Text

from common.logging_utils import configure_logging
from common.sqlalchemy import (
    check_database,
    create_base,
    create_db_engine,
    create_session_factory,
    init_schema_with_lock,
    session_scope,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://reviews_user:reviews_pass@reviews-db:5432/reviews_db",
)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "review.created")

engine = create_db_engine(DATABASE_URL)
SessionLocal = create_session_factory(engine)
Base = create_base()
LOGGER = configure_logging("reviews-service")


class ReviewDB(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    text = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OutboxEventDB(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String, index=True, nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)


class OutboxPublishError(RuntimeError):
    def __init__(self, event_id: int, topic: str, error: Exception):
        super().__init__(str(error))
        self.event_id = event_id
        self.topic = topic
        self.error = error


def init_db():
    init_schema_with_lock(engine, Base.metadata, 2001, "REVIEWS")
    LOGGER.info("event=database_initialized")


def get_database_health() -> str:
    return check_database(engine)


def create_review_with_outbox(user_id: int, item_id: str, text: str, rating: int) -> ReviewDB:
    with session_scope(SessionLocal) as db:
        created_at = datetime.utcnow()
        review = ReviewDB(
            user_id=user_id,
            item_id=item_id,
            text=text,
            rating=rating,
            created_at=created_at,
        )

        db.add(review)
        db.flush()

        event = {
            "event_type": "review.created",
            "review_id": review.id,
            "user_id": review.user_id,
            "item_id": review.item_id,
            "text": review.text,
            "rating": review.rating,
            "created_at": review.created_at.isoformat(),
        }
        db.add(
            OutboxEventDB(
                topic=KAFKA_TOPIC,
                event_type="review.created",
                payload=json.dumps(event),
                status="pending",
            )
        )
        db.commit()
        db.refresh(review)
        return review


def get_reviews_by_item(item_id: str) -> List[ReviewDB]:
    with session_scope(SessionLocal) as db:
        return (
            db.query(ReviewDB)
            .filter(ReviewDB.item_id == item_id)
            .order_by(ReviewDB.created_at.desc())
            .all()
        )


def get_reviews_by_user(user_id: int) -> List[ReviewDB]:
    with session_scope(SessionLocal) as db:
        return (
            db.query(ReviewDB)
            .filter(ReviewDB.user_id == user_id)
            .order_by(ReviewDB.created_at.desc())
            .all()
        )


def get_all_reviews() -> List[ReviewDB]:
    with session_scope(SessionLocal) as db:
        return (
            db.query(ReviewDB)
            .order_by(ReviewDB.created_at.desc())
            .all()
        )


def process_next_outbox_event(
    processor: Callable[[OutboxEventDB], None],
) -> OutboxEventDB | None:
    with session_scope(SessionLocal) as db:
        event = (
            db.query(OutboxEventDB)
            .filter(OutboxEventDB.status.in_(["pending", "failed"]))
            .order_by(OutboxEventDB.created_at.asc(), OutboxEventDB.id.asc())
            .with_for_update(skip_locked=True)
            .first()
        )
        if event is None:
            return None

        try:
            processor(event)
            event.status = "published"
            event.published_at = datetime.utcnow()
            event.last_error = None
            db.commit()
            return event
        except Exception as error:
            event.status = "failed"
            event.attempts += 1
            event.last_error = str(error)[:2000]
            db.commit()
            raise OutboxPublishError(event.id, event.topic, error) from error
