# System Architecture

## 1. Overview

Movie Review Platform is a microservice-based web application for reviewing movies and following user activity. Users can register, log in, browse a movie catalog, write reviews, follow other users, and view a personalized social feed.

The system is built using independent microservices. Each microservice registers itself in Config Server, owns its storage, and follows a three-layer architecture:

```text
API layer
Service layer
Repository layer
```

Client applications communicate with the backend only through the API Gateway.

---

## 2. High-Level Architecture

```text
Frontend / Streamlit UI
        |
        v
API Gateway
        |
        +-------------------------+-------------------------+---------------------------+
        |                         |                         |                           |
        v                         v                         v                           v
Auth Service x2           Catalog Service x2        Reviews Service x2          Feed API x2
PostgreSQL                MongoDB Replica Set       PostgreSQL + Outbox         Neo4j
       +
Redis HA: 1 master + 2 replicas,                            |
3 sentinels (quorum = 2)                                    v
                                           Outbox Publishers x2
                                                            |
                                                            v
                                     Kafka (review.created, 3 partitions)
                                                            |
                                                            v
                                            Feed Consumer x2 (same consumer group)
                                                            |
                                                            v
                                                         Neo4j
```

Every stateless HTTP tier runs **two instances** behind the API Gateway. The gateway round-robins requests across active instances resolved from Config Server and retries the alternate instance on a 5xx or transport error. Background workers are also duplicated where parallelism is safe: the **reviews outbox publisher** now runs as two workers coordinated by Postgres row locking, and the **feed consumer** runs as two workers coordinated by the Kafka consumer group.

---

## 3. Components

## 3.1 Frontend

The frontend is implemented using Streamlit.

Responsibilities:

- Provide user interface
- Support registration and login
- Display movie catalog
- Allow users to write and read reviews
- Allow users to follow other users
- Display personalized social feed
- Display system health
- Seed demo data for presentation

The frontend communicates only with the API Gateway.

Local URL:

```text
http://localhost:8501
```

---

## 3.2 API Gateway

The API Gateway is the single entry point for the frontend application.

Responsibilities:

- Route `/auth/*` requests to Auth Service
- Route `/catalog/*` requests to Catalog Service
- Route `/reviews/*` requests to Reviews Service
- Route `/feed/*` requests to Feed API
- Resolve service instances through Config Server
- Retry another active instance when a routed service instance is unavailable
- Verify JWTs before forwarding protected requests
- Provide enriched feed/review endpoints for UI composition
- Hide internal service URLs from the frontend
- Provide unified external API

Local URL:

```text
http://localhost:8000
```

Example routes:

| External route | Target service |
|---|---|
| `/auth/register` | Auth Service `/register` |
| `/auth/login` | Auth Service `/login` |
| `/catalog` | Catalog Service `/catalog` |
| `/reviews` | Reviews Service `/reviews` |
| `/feed` | Feed API `/feed` |

---

## 3.3 Auth Service

The Auth Service handles users and authentication.

Responsibilities:

- Register users
- Store password hashes
- Login users
- Generate JWT tokens
- Store active JWT token identifiers in Redis
- Verify tokens
- Logout users
- Return current user profile
- Return list of users
- Find user by username

Storage:

| Storage | Purpose |
|---|---|
| PostgreSQL | Users |
| Redis | Active JWT token identifiers |

Deployment:

- `auth-service-1`
- `auth-service-2`

Both Auth Service instances share PostgreSQL and Redis. This allows authentication failover.

---

## 3.4 Catalog Service

The Catalog Service manages movie data.

Responsibilities:

- Add movie
- Get all movies
- Get movie by id
- Search movies by title
- Search movies by genre
- Search movies by year

Storage:

```text
MongoDB Replica Set
```

MongoDB nodes:

```text
mongo1
mongo2
mongo3
```

Replica set name:

```text
rs0
```

Typical state:

```text
mongo1 -> PRIMARY
mongo2 -> SECONDARY
mongo3 -> SECONDARY
```

Deployment:

- `catalog-service-1` (port 8003)
- `catalog-service-2` (port 8013)

Both instances are stateless, register with Config Server under the same `catalog-service` name, and connect to the same Mongo replica set URI. The API Gateway resolves both via Config Server and round-robins requests; if one instance dies, the gateway retries the other.

---

## 3.5 Reviews Service

The Reviews Service stores movie reviews and writes pending `review.created` events to an outbox table in the same database transaction.

Responsibilities:

- Create review
- Store review in PostgreSQL
- Get all reviews
- Get reviews by movie
- Get reviews by user
- Queue `review.created` events in `outbox_events`

Storage:

```text
PostgreSQL
```

Deployment:

- `reviews-service-1` (port 8004)
- `reviews-service-2` (port 8014)

Both instances are stateless and share the same `reviews-db`. Each instance writes the review row and the corresponding outbox event in a single transaction (transactional outbox pattern), so duplicate inserts from concurrent clients can't make the system inconsistent.

Outbox publishers:

```text
reviews-outbox-publisher-1 and reviews-outbox-publisher-2 tail outbox_events and ship to Kafka
```


Both publishers issue `SELECT ... FOR UPDATE SKIP LOCKED` when they pick the next outbox row. Each worker holds the row lock until it either marks the row `published` or `failed`, so the other worker skips locked rows and keeps draining different work.
Kafka topic:

```text
review.created  (3 partitions)
```

---

## 3.6 Feed API And Feed Consumer

Feed is split into an HTTP API and standalone Kafka consumers.

Responsibilities:

- Create follow relationships
- Feed API returns personalized feeds and recommendations
- Feed Consumer consumes `review.created` events from Kafka
- Store graph relationships in Neo4j
- Commit Kafka offsets only after Neo4j writes succeed

Storage:

```text
Neo4j
```

Deployment:

- `feed-api-1` (port 8005), `feed-api-2` (port 8015) - stateless HTTP, behind the gateway
- `feed-consumer-1`, `feed-consumer-2` - same Kafka consumer group `feed-service-consumer-group`

The two Feed Consumer instances belong to a single consumer group. Kafka assigns partitions of the `review.created` topic (3 partitions) between them, so under normal load each consumer processes ~half the events in parallel. When a consumer dies, Kafka triggers a **consumer group rebalance**: the surviving consumer is assigned all 3 partitions within a few seconds and processing continues without operator action. When the failed consumer comes back up, partitions are rebalanced again.

Graph model:

```text
(User)-[:FOLLOWS]->(User)
(User)-[:WROTE]->(Review)
(Review)-[:ABOUT]->(Item)
(User)-[:REVIEWED]->(Item)
```

---

## 3.7 Kafka

Kafka is used for asynchronous communication between the Reviews Outbox Publisher and Feed Consumer.

Topic:

```text
review.created
```

Producer:

```text
Reviews Service
```

Consumer:

```text
Feed Consumer
```

Purpose:

- Decouple review creation from feed update
- Allow Reviews Service to work without directly calling Feed API or Feed Consumer
- Demonstrate asynchronous message-based processing

---

## 3.8 Neo4j

Neo4j stores social graph data.

Node labels:

| Label | Meaning |
|---|---|
| User | Platform user |
| Review | Movie review |
| Item | Movie item |

Relationship types:

| Relationship | Meaning |
|---|---|
| FOLLOWS | User follows another user |
| WROTE | User wrote a review |
| ABOUT | Review is about a movie |
| REVIEWED | User reviewed a movie |

Example query:

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50;
```

---

# 4. Data Ownership

Each microservice owns its own data.

| Service | Database | Data |
|---|---|---|
| Auth Service | PostgreSQL | Users |
| Auth Service | Redis | Active JWT tokens |
| Catalog Service | MongoDB Replica Set | Movies |
| Reviews Service | PostgreSQL | Reviews |
| Feed API / Feed Consumer | Neo4j | Social graph |

This follows the database-per-service pattern.

---

# 5. Communication

## 5.1 Synchronous Communication

Synchronous communication is used for client-facing operations.

```text
Frontend -> API Gateway -> Microservice
```

Examples:

- Register user
- Login
- Get catalog
- Search movies
- Create review
- Get feed

---

## 5.2 Asynchronous Communication

Asynchronous communication is used for review event processing.

```text
Reviews Service -> outbox_events -> Reviews Outbox Publishers -> Kafka -> Feed Consumer
```

Flow:

```text
1. User creates review.
2. Reviews Service stores review in PostgreSQL.
3. Reviews Service writes a review.created outbox event in the same transaction.
4. One Reviews Outbox Publisher instance locks the next pending row and publishes the event to Kafka.
5. Feed Consumer consumes the event and updates Neo4j, then commits the Kafka offset.
```

---

# 6. Fault Tolerance

## 6.1 Stateless Application Tiers (Auth, Catalog, Reviews, Feed API)

Every application tier runs two stateless instances and shares storage:

| Service | Instances | Shared backing store |
|---|---|---|
| auth-service | `auth-service-1`, `auth-service-2` | Postgres `auth-db` + Redis (Sentinel-managed) |
| catalog-service | `catalog-service-1`, `catalog-service-2` | MongoDB replica set `rs0` |
| reviews-service | `reviews-service-1`, `reviews-service-2` | Postgres `reviews-db` (with outbox table) |
| feed-api | `feed-api-1`, `feed-api-2` | Neo4j |

All instances register with Config Server under one logical service name. The API Gateway resolves the active instance list via `GET /services/{name}`, then in `call_service` iterates over instances and retries the next one on any transport error or 5xx response. So a `docker stop <instance>` is invisible to the caller after one retry - the user-facing API never returns an error for an instance loss, as long as at least one peer is still alive.

Failover scenario (works the same for every tier above):

```text
1. Client makes a request to the API Gateway.
2. Gateway calls Config Server: GET /services/<service>.
3. Gateway tries instance #1.
4. If instance #1 is down (connection refused or 5xx),
   gateway retries on instance #2.
5. Client sees a successful response.
```

For Auth specifically: because the active-token-id whitelist lives in Sentinel-managed Redis (not in service memory), a token issued by `auth-service-1` can be verified by `auth-service-2`.

---

## 6.2 Redis HA via Sentinel

Redis stores the active JWT token whitelist for the Auth Service. It is a critical dependency: if Redis is unreachable, `verify_token` fails and every protected endpoint returns 401, regardless of how many Auth Service instances are running. A single Redis container is therefore a single point of failure for the entire auth flow.

The deployed topology is:

```text
redis-master            (writable)
redis-replica-1         (read-only async replica)
redis-replica-2         (read-only async replica)
redis-sentinel-1
redis-sentinel-2        (monitor master, quorum = 2)
redis-sentinel-3
```

Auth Service connects via the three sentinels rather than directly to a Redis node. It does that through a shared Redis client helper in `common`, which builds a Sentinel-backed `redis-py` client. Under the hood, Redis Sentinel support re-resolves the current master on each connection acquisition, so:

```text
1. redis-master goes down.
2. Within `down-after-milliseconds` (5s), sentinels mark it +sdown.
3. Sentinels reach quorum (2 of 3) and declare +odown.
4. A leader sentinel is elected.
5. The leader promotes one replica to master (~5-10s).
6. Auth Service's next request fails once, retries, gets the new
   master from a sentinel, succeeds.
```

The previous master, when it comes back up, is automatically reconfigured as a replica of the new master.

Trade-off: this is asynchronous replication, so up to a few hundred ms of writes accepted by the old master could be lost in a fail-over. For a token whitelist that's acceptable - the worst case is a freshly issued token that needs to be re-issued by re-logging in.

---

## 6.3 Reviews Outbox Publisher (Two Instances, Row-Locked)

The two reviews-service HTTP instances both insert into `outbox_events` in their request transaction, and now **two** outbox publishers read from that table and forward rows to Kafka.

Safety comes from the publisher-side query: each worker processes one row inside a database transaction and selects it with `FOR UPDATE SKIP LOCKED`. While publisher A is sending row N to Kafka, publisher B skips row N and claims a different pending row. Only after the publish succeeds does the transaction mark the row as `published` and commit. On publish failure the same transaction marks the row `failed`, increments `attempts`, and releases it for retry.

This keeps the behavior at-least-once, which matches the rest of the pipeline: if a publisher crashes after Kafka acknowledges the send but before the Postgres transaction commits, the row is retried and Kafka may see the event again. That is acceptable here because the Feed Consumer writes through idempotent Neo4j `MERGE` operations.

---

## 6.4 MongoDB Replica Set

The Catalog Service uses a three-node MongoDB Replica Set (`mongo1`, `mongo2`, `mongo3`, all running with `--replSet rs0`). The replica set is bootstrapped automatically on first start by a one-shot `mongo-init` service defined in `docker-compose.yml`, which is idempotent - on subsequent starts it detects that `rs0` is already initialised and exits without changes. `catalog-service` declares `depends_on: mongo-init: service_completed_successfully`, so it never starts until the replica set has a PRIMARY elected.

Benefits:

- Data replication
- Primary-secondary architecture
- Automatic primary election when quorum is available
- Improved fault tolerance for catalog data
- Automated one-command bootstrap (no manual `rs.initiate()` step)

Replica set check from the host:

```powershell
docker exec -it mongo1 mongosh --quiet --eval "rs.status().members.map(m => m.name + ' ' + m.stateStr)"
```

Expected result:

```javascript
[
  { name: 'mongo1:27017', state: 'PRIMARY' },
  { name: 'mongo2:27017', state: 'SECONDARY' },
  { name: 'mongo3:27017', state: 'SECONDARY' }
]
```

---

# 7. Deployment

The system is deployed locally using Docker Compose.

Main services:

```text
frontend
api-gateway
config-server
auth-service-1
auth-service-2
catalog-service-1
catalog-service-2
reviews-service-1
reviews-service-2
reviews-outbox-publisher-1
reviews-outbox-publisher-2
feed-api-1
feed-api-2
feed-consumer-1
feed-consumer-2
auth-db
reviews-db
redis-master
redis-replica-1
redis-replica-2
redis-sentinel-1
redis-sentinel-2
redis-sentinel-3
mongo1
mongo2
mongo3
mongo-init     (one-shot, exits 0 after rs.initiate)
zookeeper
kafka
neo4j
```

Run command:

```powershell
docker compose up -d --build
```

---

# 8. Ports

| Component | Host port |
|---|---|
| Frontend | 8501 |
| API Gateway | 8000 |
| Auth Service 1 | 8001 |
| Auth Service 2 | 8002 |
| Catalog Service 1 | 8003 |
| Catalog Service 2 | 8013 |
| Reviews Service 1 | 8004 |
| Reviews Service 2 | 8014 |
| Feed API 1 | 8005 |
| Feed API 2 | 8015 |
| Config Server | 8010 |
| Neo4j Browser | 7474 |
| Neo4j Bolt | 7687 |
| Redis Master | 6379 |
| Redis Sentinel 1/2/3 | 26379 (in-cluster only) |
| Kafka | 9092 |
| PostgreSQL Auth DB | 5433 |
| PostgreSQL Reviews DB | 5434 |
| MongoDB node 1 | 27017 |
| MongoDB node 2 | 27018 |
| MongoDB node 3 | 27019 |

---

# 9. Three-Layer Microservice Structure

Each service follows the same general structure:

```text
service-name/
  app/
    main.py
    api.py
    service.py
    repository.py
    models.py
  Dockerfile
  requirements.txt
```

## API Layer

Responsible for:

- HTTP endpoints
- Request validation
- Response formatting

## Service Layer

Responsible for:

- Business logic
- Authentication logic
- Event publishing
- Data transformation

## Repository Layer

Responsible for:

- Database connection
- Queries
- Persistence logic

---

# 10. Architecture Benefits

The selected architecture provides:

- Independent microservice development
- Database-per-service separation
- Fault-tolerant authentication
- NoSQL replication
- Asynchronous event processing
- Clear separation of responsibilities
- Graph-based social feed
- Easy local deployment with Docker Compose
- Demonstrable distributed system behavior
