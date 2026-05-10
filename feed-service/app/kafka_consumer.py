import json
import os
import time
import threading

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from app.repository import save_review_event


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "review.created")


def consume_reviews():
    consumer = None
    max_attempts = 20

    for attempt in range(1, max_attempts + 1):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="feed-service-consumer-group"
            )
            print("[FEED] Kafka consumer connected successfully", flush=True)
            break

        except NoBrokersAvailable:
            print(f"[FEED] Kafka not ready, attempt {attempt}/{max_attempts}", flush=True)
            time.sleep(2)

    if consumer is None:
        raise RuntimeError("Kafka is not available after retries")

    for message in consumer:
        event = message.value

        if event.get("event_type") == "review.created":
            save_review_event(event)
            print(f"[FEED] Consumed review.created event: {event}", flush=True)


def start_consumer_thread():
    thread = threading.Thread(target=consume_reviews, daemon=True)
    thread.start()
    print("[FEED] Kafka consumer thread started", flush=True)