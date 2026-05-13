# Event Specification

## 1. Overview

The Movie Review Platform uses Kafka for asynchronous communication between the Reviews outbox publisher and Feed Consumer.

The main event is created when a user writes a review.

## 2. Topic

```text
review.created
```

## 3. Producer

```text
Reviews Outbox Publisher
```

## 4. Consumer

```text
Feed Consumer
```

## 5. Event Payload

```json
{
  "event_type": "review.created",
  "review_id": 1,
  "user_id": 1,
  "item_id": "movie-id",
  "text": "Great movie with strong atmosphere.",
  "rating": 9,
  "created_at": "2026-05-10T13:05:03.411227"
}
```

## 6. Field Description

| Field | Type | Description |
|---|---|---|
| event_type | string | Event name, always `review.created` |
| review_id | integer | Created review id |
| user_id | integer | Author user id |
| item_id | string | Movie id |
| text | string | Review text |
| rating | integer | Rating from 1 to 10 |
| created_at | string | Review creation timestamp |

## 7. Event Flow

```text
User writes review
  ↓
Reviews Service stores review in PostgreSQL and writes an outbox event in the same transaction
  ↓
Reviews Outbox Publisher reads the pending outbox event
  ↓
Kafka stores event in review.created topic
  ↓
Feed Consumer consumes event
  ↓
Feed Consumer writes graph data to Neo4j and commits the Kafka offset
```

## 8. Feed Consumer Processing Rules

When Feed Consumer receives `review.created`, it must:

1. Create or update User node.
2. Create or update Item node.
3. Create or update Review node.
4. Create relationship `(User)-[:WROTE]->(Review)`.
5. Create relationship `(Review)-[:ABOUT]->(Item)`.
6. Create relationship `(User)-[:REVIEWED]->(Item)`.

## 9. Idempotency

Neo4j operations use `MERGE`, so consuming the same event again should not create duplicate User, Item, or Review nodes with the same ids.

The consumer uses manual Kafka offset commits. It commits an offset only after the Neo4j write succeeds. If Neo4j write or offset commit fails, the process exits/restarts and Kafka redelivers the uncommitted message.

## 10. Verification

Reviews Outbox Publisher logs should contain:

```text
[REVIEWS-OUTBOX] Published event
```

Feed Consumer logs should contain:

```text
[FEED-CONSUMER] Consumed review.created event
```

Kafka topic check:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list
```

Expected topic:

```text
review.created
```
