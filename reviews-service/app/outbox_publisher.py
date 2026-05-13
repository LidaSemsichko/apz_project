import json
import os
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from common.logging_utils import configure_logging
from common.retry import retry
from app.repository import (
    get_pending_outbox_events,
    init_db,
    mark_outbox_failed,
    mark_outbox_published,
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
POLL_INTERVAL_SECONDS = float(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "2"))
LOGGER = configure_logging("reviews-outbox")


def create_kafka_producer() -> KafkaProducer:
    def operation():
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
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


def publish_event(producer: KafkaProducer, event) -> None:
    payload = json.loads(event.payload)
    future = producer.send(event.topic, payload)
    future.get(timeout=10)
    producer.flush()


def run_forever() -> None:
    init_db()
    producer = create_kafka_producer()
    LOGGER.info("event=outbox_publisher_started")

    while True:
        events = get_pending_outbox_events()
        if not events:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        for event in events:
            try:
                publish_event(producer, event)
                mark_outbox_published(event.id)
                LOGGER.info(
                    "event=outbox_published outbox_event_id=%s topic=%s",
                    event.id,
                    event.topic,
                )
            except Exception as error:
                mark_outbox_failed(event.id, str(error))
                LOGGER.exception(
                    "event=outbox_event_publish_failed outbox_event_id=%s error=%s",
                    event.id,
                    error,
                )
                time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
