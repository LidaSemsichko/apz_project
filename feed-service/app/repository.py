import os
from typing import List

from neo4j import GraphDatabase

from common.logging_utils import configure_logging
from common.retry import retry


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

_driver = None
LOGGER = configure_logging("feed-service")


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
    return _driver


def wait_for_neo4j():
    def operation() -> None:
        with get_driver().session() as session:
            session.run("RETURN 1")

    retry(
        operation,
        attempts=20,
        delay_seconds=2,
        on_retry=lambda attempt, error: LOGGER.warning(
            "event=neo4j_not_ready attempt=%s max_attempts=20 error=%s",
            attempt,
            error,
        ),
    )
    LOGGER.info("event=neo4j_connected")


def get_database_health() -> str:
    try:
        with get_driver().session() as session:
            session.run("RETURN 1")
        return "ok"
    except Exception:
        return "unavailable"


def create_constraints():
    with get_driver().session() as session:
        session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT item_id_unique IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE")
        session.run("CREATE CONSTRAINT review_id_unique IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE")


def follow_user(follower_id: int, following_id: int):
    with get_driver().session() as session:
        session.run(
            """
            MERGE (follower:User {id: $follower_id})
            MERGE (following:User {id: $following_id})
            MERGE (follower)-[:FOLLOWS]->(following)
            """,
            follower_id=follower_id,
            following_id=following_id,
        )


def save_review_event(event: dict):
    with get_driver().session() as session:
        session.run(
            """
            MERGE (u:User {id: $user_id})
            MERGE (i:Item {id: $item_id})
            MERGE (r:Review {id: $review_id})
            SET r.text = $text,
                r.rating = $rating,
                r.created_at = $created_at
            MERGE (u)-[:WROTE]->(r)
            MERGE (r)-[:ABOUT]->(i)
            MERGE (u)-[:REVIEWED]->(i)
            """,
            user_id=int(event["user_id"]),
            item_id=str(event["item_id"]),
            review_id=int(event["review_id"]),
            text=event["text"],
            rating=int(event["rating"]),
            created_at=event["created_at"],
        )


def get_feed_for_user(user_id: int) -> List[dict]:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (me:User {id: $user_id})-[:FOLLOWS]->(author:User)-[:WROTE]->(r:Review)-[:ABOUT]->(i:Item)
            RETURN r.id AS review_id,
                   author.id AS user_id,
                   i.id AS item_id,
                   r.text AS text,
                   r.rating AS rating,
                   r.created_at AS created_at
            ORDER BY r.created_at DESC
            LIMIT 50
            """,
            user_id=user_id,
        )

        return [record.data() for record in result]


def get_user_reviews(user_id: int) -> List[dict]:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (u:User {id: $user_id})-[:WROTE]->(r:Review)-[:ABOUT]->(i:Item)
            RETURN r.id AS review_id,
                   u.id AS user_id,
                   i.id AS item_id,
                   r.text AS text,
                   r.rating AS rating,
                   r.created_at AS created_at
            ORDER BY r.created_at DESC
            LIMIT 50
            """,
            user_id=user_id,
        )

        return [record.data() for record in result]


def get_recommendations(user_id: int) -> List[dict]:
    with get_driver().session() as session:
        result = session.run(
            """
            MATCH (me:User {id: $user_id})-[:REVIEWED]->(item:Item)<-[:REVIEWED]-(other:User)-[:REVIEWED]->(recommended:Item)
            WHERE NOT (me)-[:REVIEWED]->(recommended)
            RETURN recommended.id AS item_id,
                   count(*) AS score
            ORDER BY score DESC
            LIMIT 10
            """,
            user_id=user_id,
        )

        return [record.data() for record in result]
