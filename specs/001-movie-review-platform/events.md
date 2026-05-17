# Event Specification

## 1. Overview

The Movie Review Platform uses Kafka for asynchronous communication between the Reviews outbox publisher and Feed Consumer.

The main event is created when a user writes a review.

## 2. Topic

```text
review.created
```

Partition count: 3 (`KAFKA_NUM_PARTITIONS=3` on the broker). This is intentionally larger than the current consumer count (2) so partitions can be split across consumers AND we have headroom to add a third consumer without changing the topic.

## 3. Producer

```text
Reviews Outbox Publisher x2
```

The two `reviews-service-{1,2}` HTTP instances both insert into the `outbox_events` table inside their request transactions. Two outbox publishers tail the table and publish pending rows to Kafka. They coordinate with `SELECT ... FOR UPDATE SKIP LOCKED`, so each worker locks a different pending row while it publishes.

## 4. Consumers

```text
feed-consumer-1  | both join Kafka consumer group
feed-consumer-2  | "feed-service-consumer-group"
```

Kafka assigns the 3 partitions across the two consumers. On consumer leave/join Kafka triggers a rebalance and reassigns the partitions; offsets are committed to `__consumer_offsets` so the survivor resumes exactly where the failed consumer stopped.

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
One Reviews Outbox Publisher instance locks and reads the pending outbox event
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

## 9. Idempotency and Delivery Guarantees

Neo4j operations use `MERGE`, so consuming the same event again should not create duplicate User, Item, or Review nodes with the same ids.

The consumer uses manual Kafka offset commits. It commits an offset only after the Neo4j write succeeds. If Neo4j write or offset commit fails, the process exits/restarts and Kafka redelivers the uncommitted message. Combined with idempotent `MERGE`, this gives effectively at-least-once delivery with safe replay.

When a consumer dies, Kafka triggers a group rebalance and reassigns the partition(s) the dead consumer owned to the surviving consumer. Because offsets are committed to Kafka rather than held in consumer memory, the survivor resumes from exactly where the dead consumer last committed — no duplicate writes and no lost events under normal conditions.

## 10. Verification

Reviews Outbox Publisher logs should contain:

```text
event=outbox_published
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
