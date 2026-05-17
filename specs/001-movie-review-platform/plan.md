# Implementation Plan: Movie Review Platform

## 1. Architecture Decision

The system is implemented as a set of independent microservices connected through an API Gateway.

Architecture:

```text
Frontend
  ↓
API Gateway
  ↓
Auth / Catalog / Reviews / Feed
  ↓
PostgreSQL / Redis / MongoDB / Kafka / Neo4j
```

## 2. Technology Stack

| Component | Technology |
|---|---|
| Backend framework | FastAPI |
| Frontend | Streamlit |
| Auth database | PostgreSQL |
| Reviews database | PostgreSQL |
| Catalog database | MongoDB Replica Set |
| Token storage | Redis (1 master + 2 replicas, 3 sentinels) |
| Message queue | Kafka (review.created topic, 3 partitions) |
| Graph database | Neo4j |
| Deployment | Docker Compose |

## 3. Service Plan

## 3.1 API Gateway

Purpose:

- Single entry point for frontend
- Route requests to internal services

Implementation:

- FastAPI
- httpx for proxy requests

Routes:

- `/auth/*`
- `/catalog/*`
- `/reviews/*`
- `/feed/*`

## 3.2 Auth Service

Purpose:

- User management
- Authentication
- Token lifecycle

Storage:

- PostgreSQL for users
- Redis (Sentinel-managed, see §6) for active token ids

Endpoints:

- `/register`
- `/login`
- `/logout`
- `/verify`
- `/me`
- `/users`
- `/users/by-username/{username}`

Deployment:

- Instances: `auth-service-1` (host port 8001), `auth-service-2` (8002)
- Shared Postgres `auth-db`
- Redis access goes through a shared Sentinel-aware Redis client helper, so a Redis master failover is transparent to the application after a single retry.

## 3.3 Catalog Service

Purpose:

- Movie catalog
- Movie search

Storage:

- MongoDB Replica Set

Endpoints:

- `/catalog`
- `/catalog/{movie_id}`
- `/catalog/search`

Deployment:

- Instances: `catalog-service-1` (host port 8003), `catalog-service-2` (8013)
- Both stateless; both connect to the same Mongo replica-set URI and rely on Mongo's driver-side primary discovery for writes.

## 3.4 Reviews Service

Purpose:

- Store reviews
- Queue review events via transactional outbox

Storage:

- PostgreSQL (`reviews-db`)
- `outbox_events` table in the same database

Messaging:

- Kafka producer (via the two-instance Reviews Outbox Publisher)

Endpoints:

- `/reviews`
- `/reviews/item/{item_id}`
- `/reviews/user/{user_id}`

Deployment:

- HTTP tier: `reviews-service-1` (8004), `reviews-service-2` (8014). Both write the review row and the outbox event in a single Postgres transaction, so concurrent writes from both instances are safe.
- Outbox Publisher: `reviews-outbox-publisher-1` and `reviews-outbox-publisher-2`. Each worker reads one pending row at a time with `FOR UPDATE SKIP LOCKED`, so they publish in parallel without claiming the same outbox event.

## 3.5 Feed Service

Purpose:

- Follow users
- Personalized feed
- Recommendations
- Kafka event consumption

Storage:

- Neo4j

Messaging:

- Kafka consumer

Endpoints:

- `/follow/{following_id}`
- `/feed`
- `/recommendations`

Deployment:

- HTTP tier: `feed-api-1` (8005), `feed-api-2` (8015). Stateless; both serve all feed/follow endpoints.
- Consumer tier: `feed-consumer-1`, `feed-consumer-2`. Both join Kafka consumer group `feed-service-consumer-group`. Kafka assigns the 3 partitions of `review.created` across them (typically 2:1 or 1:2). When a consumer leaves, Kafka triggers a rebalance and the survivor is assigned all 3 partitions. When it rejoins, partitions are split again. Offsets are committed manually after Neo4j writes succeed (at-least-once delivery; idempotent thanks to Neo4j `MERGE`).

## 3.6 Frontend

Purpose:

- Browser UI
- Login gate
- Catalog browsing
- Review creation
- Feed viewing
- Demo seeding

Technology:

- Streamlit

## 4. Data Design

### User

Stored in Auth PostgreSQL.

```text
id
email
username
password_hash
created_at
```

### Movie

Stored in MongoDB.

```text
id
title
description
genres
year
director
poster_url
```

### Review

Stored in Reviews PostgreSQL.

```text
id
user_id
item_id
text
rating
created_at
```

### Graph

Stored in Neo4j.

```text
(User)-[:FOLLOWS]->(User)
(User)-[:WROTE]->(Review)
(Review)-[:ABOUT]->(Item)
(User)-[:REVIEWED]->(Item)
```

## 5. Event Design

Kafka topic:

```text
review.created
```

Producer:

```text
Reviews Service
```

Consumer:

```text
Feed Service
```

Payload:

```json
{
  "event_type": "review.created",
  "review_id": 1,
  "user_id": 1,
  "item_id": "movie-id",
  "text": "Review text",
  "rating": 9,
  "created_at": "timestamp"
}
```

## 6. Fault Tolerance Plan

### 6.1 Stateless Application Tiers

Every application tier runs two instances and shares its backing store:

| Tier | Instances | Shared backing store |
|---|---|---|
| auth-service | `auth-service-1`, `auth-service-2` | Postgres `auth-db` + Sentinel-managed Redis |
| catalog-service | `catalog-service-1`, `catalog-service-2` | Mongo replica set `rs0` |
| reviews-service | `reviews-service-1`, `reviews-service-2` | Postgres `reviews-db` (with outbox) |
| feed-api | `feed-api-1`, `feed-api-2` | Neo4j |

All instances register with Config Server under one logical service name. The API Gateway resolves the active instance list via `GET /services/{name}`, iterates in `call_service`, and retries the next instance on any transport error or 5xx response. Therefore a `docker stop <instance>` is invisible to the caller after one retry.

### 6.2 Redis Sentinel HA

Redis is the only single-process dependency of the auth flow (active-token whitelist). Topology:

```text
redis-master        (writable)
redis-replica-1     (async read-only)
redis-replica-2     (async read-only)
redis-sentinel-1
redis-sentinel-2    (3 sentinels, quorum = 2)
redis-sentinel-3
```

Sentinel parameters: `down-after-milliseconds=5000`, `failover-timeout=10000`, `parallel-syncs=1`. Total wall-clock for a master failover is approximately 5-15 seconds. Auth Service uses a shared Sentinel-aware Redis client helper, and the underlying `redis-py` Sentinel support re-resolves the master on each connection acquisition, so the application reconnects to the new master after the next operation without any restart.

Trade-off: replication is asynchronous, so up to a few hundred milliseconds of writes accepted by the old master may be lost during a failover. For a token whitelist this is acceptable (worst case: a just-issued token must be re-issued by logging in again).

### 6.3 Reviews Outbox Publisher - Two Instances With Row Locking

The two reviews-service HTTP instances both write `outbox_events` rows inside their request transactions, and two publishers read from that table and forward rows to Kafka.

Each publisher processes one row inside a database transaction and claims it with `FOR UPDATE SKIP LOCKED`. The row stays locked until the publisher marks it `published` or `failed`, so the peer worker skips that row and keeps draining other pending events. On a crash the transaction is rolled back and the row becomes visible again, which preserves at-least-once delivery without stranding work.

### 6.4 Kafka Consumer Group

`review.created` is created with 3 partitions (`KAFKA_NUM_PARTITIONS=3` on the broker). Both Feed Consumer instances share consumer group `feed-service-consumer-group`. Kafka's group coordinator assigns partitions across them; on consumer leave/join it triggers a rebalance and re-assigns. Offsets are committed manually to `__consumer_offsets` after a successful Neo4j write, so the survivor resumes exactly where the failed consumer stopped. Partition count is intentionally larger than current consumer count to leave headroom for adding a third consumer without changing the topic.

### 6.5 MongoDB Replica Set

The replica set is bootstrapped automatically by a one-shot `mongo-init` service in `docker-compose.yml`. The init script is idempotent: it checks `rs.status()` first and exits cleanly when `rs0` is already initialised, so it is safe to re-run on every `docker compose up`. `catalog-service-{1,2}` depend on `mongo-init: service_completed_successfully` and therefore never start before the replica set has a PRIMARY.

Expected steady state:

```text
mongo1 -> PRIMARY
mongo2 -> SECONDARY
mongo3 -> SECONDARY
```

### 6.6 Compose Healthchecks

All stateful services (`auth-db`, `reviews-db`, all 3 redis nodes, all 3 sentinels, `mongo1/2/3`, `zookeeper`, `kafka`, `neo4j`) declare a `healthcheck:` block. Application services use `depends_on: condition: service_healthy` so they only start after their dependencies are actually accepting connections, not merely after the container has launched.

### 6.7 Secrets Hygiene

Credentials (`JWT_SECRET`, `AUTH_POSTGRES_*`, `REVIEWS_POSTGRES_*`, `NEO4J_USER`, `NEO4J_PASSWORD`) live in a `.env` file that is git-ignored. `docker-compose.yml` references them as `${VAR}`. A committed `.env.example` documents the variable set and the local-dev defaults. In production every value must be overridden via the deployment platform's secret store.

### 6.8 Continuous Integration

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

```text
- compose-config:   provisions .env from .env.example, runs `docker compose config`, fails on any unset ${VAR}
- python-syntax:    `python -m compileall` across every service
- docker-build:     matrix build of every service's Docker image
```

## 7. Implementation Steps

### Phase A — Initial system

1. Create Docker Compose infrastructure
2. Implement Auth Service
3. Add Redis token storage
4. Add second Auth instance
5. Implement Catalog Service
6. Configure MongoDB Replica Set (auto-bootstrap via `mongo-init`)
7. Implement Reviews Service
8. Add Kafka producer (transactional outbox pattern)
9. Implement Feed Service
10. Add Kafka consumer
11. Add Neo4j graph model
12. Implement API Gateway
13. Implement Streamlit UI
14. Add demo data seeding
15. Add compose healthchecks
16. Add CI workflow (`.github/workflows/ci.yml`)
17. Add documentation
18. Test all demo scenarios

### Phase B — Horizontal scaling and HA

19. Scale catalog-service to 2 instances
20. Scale reviews-service to 2 instances (keep outbox publisher as singleton)
21. Scale feed-api and feed-consumer to 2 instances each (same consumer group, `KAFKA_NUM_PARTITIONS=3`)
22. Replace single Redis with master + 2 replicas + 3 sentinels; switch auth-service to a shared Sentinel-aware Redis client helper
23. Move credentials out of `docker-compose.yml` into `.env` (git-ignored), commit `.env.example`, update CI to substitute and fail on unset `${VAR}`
24. Add `docs/testing-scenarios.md` covering failover for every tier, Kafka consumer-group rebalancing, and Redis Sentinel master promotion

## 8. Validation Plan

The implementation is valid if:

- All containers start (28 long-running + 1 one-shot `mongo-init` that exits 0)
- Health endpoints return ok
- Config Server reports 2 instances for each of: `auth-service`, `catalog-service`, `reviews-service`, `feed-api`
- User can register and log in
- Logout invalidates token
- Stopping one instance of any tier does not interrupt service after a single retry
- Movies can be created and searched
- Reviews can be created
- Kafka receives review events
- Both Feed Consumers are active in the consumer group and Kafka rebalances partitions on consumer leave/join
- Stopping `redis-master` triggers a Sentinel-managed failover; `auth/health` reports the new master within 15s
- Neo4j graph contains relationships
- UI can demonstrate full flow
- CI passes (compose-config with `.env.example` substitution, python-syntax, matrix docker-build)
