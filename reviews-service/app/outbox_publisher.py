import json
import os
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from common.logging_utils import configure_logging
from common.retry import retry
from app.repository import (
    init_db,
    OutboxPublishError,
    process_next_outbox_event,
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
POLL_INTERVAL_SECONDS = float(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "2"))
BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "20"))
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "reviews-outbox-publisher")
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
    LOGGER.info(
        "event=outbox_publisher_started instance=%s batch_size=%s",
        INSTANCE_NAME,
        BATCH_SIZE,
    )

    while True:
        processed = 0
        publish_failed = False

        for _ in range(BATCH_SIZE):
            try:
                event = process_next_outbox_event(
                    lambda current_event: publish_event(producer, current_event)
                )
            except OutboxPublishError as error:
                publish_failed = True
                LOGGER.exception(
                    "event=outbox_event_publish_failed instance=%s outbox_event_id=%s topic=%s error=%s",
                    INSTANCE_NAME,
                    error.event_id,
                    error.topic,
                    error.error,
                )
                time.sleep(POLL_INTERVAL_SECONDS)
                break

            if event is None:
                break

            processed += 1
            LOGGER.info(
                "event=outbox_published instance=%s outbox_event_id=%s topic=%s",
                INSTANCE_NAME,
                event.id,
                event.topic,
            )

        if processed == 0 and not publish_failed:
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
