import json
import os
import time

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from common.logging_utils import configure_logging
from common.retry import retry
from app.repository import create_constraints, save_review_event, wait_for_neo4j


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "review.created")
LOGGER = configure_logging("feed-consumer")


def create_consumer() -> KafkaConsumer:
    def operation():
        return KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id="feed-service-consumer-group",
        )

    return retry(
        operation,
        attempts=20,
        delay_seconds=2,
        exceptions=(NoBrokersAvailable,),
        on_retry=lambda attempt, error: LOGGER.warning(
            "event=kafka_not_ready attempt=%s max_attempts=20 error=%s",
            attempt,
            error,
        ),
    )


def consume_reviews():
    wait_for_neo4j()
    create_constraints()
    consumer = create_consumer()
    LOGGER.info("event=kafka_consumer_connected topic=%s", KAFKA_TOPIC)

    for message in consumer:
        event = message.value
        try:
            if event.get("event_type") == "review.created":
                save_review_event(event)
                LOGGER.info(
                    "event=review_created_consumed review_id=%s user_id=%s item_id=%s",
                    event.get("review_id"),
                    event.get("user_id"),
                    event.get("item_id"),
                )
            consumer.commit()
        except Exception as error:
            LOGGER.exception("event=processing_failed_offset_not_committed error=%s", error)
            time.sleep(2)
            raise


if __name__ == "__main__":
    consume_reviews()
