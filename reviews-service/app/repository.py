import os
import time
from datetime import datetime
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://reviews_user:reviews_pass@reviews-db:5432/reviews_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


class ReviewDB(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    text = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    max_attempts = 15

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("SELECT pg_advisory_lock(2001)")
                try:
                    Base.metadata.create_all(bind=connection)
                finally:
                    connection.exec_driver_sql("SELECT pg_advisory_unlock(2001)")

            print("[REVIEWS] Database initialized successfully", flush=True)
            return

        except OperationalError:
            print(f"[REVIEWS] Database not ready, attempt {attempt}/{max_attempts}", flush=True)
            time.sleep(2)

    raise RuntimeError("Reviews database is not available after retries")


def create_review(user_id: int, item_id: str, text: str, rating: int) -> ReviewDB:
    db = SessionLocal()
    try:
        review = ReviewDB(
            user_id=user_id,
            item_id=item_id,
            text=text,
            rating=rating
        )

        db.add(review)
        db.commit()
        db.refresh(review)

        return review
    finally:
        db.close()


def get_reviews_by_item(item_id: str) -> List[ReviewDB]:
    db = SessionLocal()
    try:
        return (
            db.query(ReviewDB)
            .filter(ReviewDB.item_id == item_id)
            .order_by(ReviewDB.created_at.desc())
            .all()
        )
    finally:
        db.close()


def get_reviews_by_user(user_id: int) -> List[ReviewDB]:
    db = SessionLocal()
    try:
        return (
            db.query(ReviewDB)
            .filter(ReviewDB.user_id == user_id)
            .order_by(ReviewDB.created_at.desc())
            .all()
        )
    finally:
        db.close()


def get_all_reviews() -> List[ReviewDB]:
    db = SessionLocal()
    try:
        return (
            db.query(ReviewDB)
            .order_by(ReviewDB.created_at.desc())
            .all()
        )
    finally:
        db.close()