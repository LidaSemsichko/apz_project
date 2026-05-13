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
        v
Config Server
        |
        +------------------------+-------------------------+----------------------+
        |                        |                         |                      |
        v                        v                         v                      v
Auth Service              Catalog Service           Reviews Service        Feed API
PostgreSQL + Redis        MongoDB Replica Set       PostgreSQL + Outbox    Neo4j
                                                    |
                                                    v
                                             Outbox Publisher -> Kafka -> Feed Consumer -> Neo4j
```

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

Outbox publisher:

```text
reviews-outbox-publisher publishes queued events to Kafka
```

Kafka topic:

```text
review.created
```

---

## 3.6 Feed API And Feed Consumer

Feed is split into an HTTP API and a standalone Kafka consumer.

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
Reviews Service -> outbox_events -> Reviews Outbox Publisher -> Kafka -> Feed Consumer
```

Flow:

```text
1. User creates review.
2. Reviews Service stores review in PostgreSQL.
3. Reviews Service writes a review.created outbox event in the same transaction.
4. Reviews Outbox Publisher publishes the event to Kafka.
5. Feed Consumer consumes the event and updates Neo4j, then commits the Kafka offset.
```

---

# 6. Fault Tolerance

## 6.1 Auth Service Failover

The Auth Service is deployed in two instances:

```text
auth-service-1
auth-service-2
```

JWT token identifiers are stored in Redis. Because token state is stored in Redis and not in local service memory, another Auth Service instance can continue validating tokens if one instance fails.

Failover scenario:

```text
1. User logs in through the API Gateway.
2. Token id is stored in Redis.
3. auth-service-1 is stopped.
4. User verifies the same token through the API Gateway.
5. The gateway resolves auth-service-2 through Config Server, and auth-service-2 validates token state using Redis.
```

---

## 6.2 MongoDB Replica Set

The Catalog Service uses a three-node MongoDB Replica Set (`mongo1`, `mongo2`, `mongo3`, all running with `--replSet rs0`). The replica set is bootstrapped automatically on first start by a one-shot `mongo-init` service defined in `docker-compose.yml`, which is idempotent — on subsequent starts it detects that `rs0` is already initialised and exits without changes. `catalog-service` declares `depends_on: mongo-init: service_completed_successfully`, so it never starts until the replica set has a PRIMARY elected.

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
auth-service-1
auth-service-2
catalog-service
reviews-service
feed-api
feed-consumer
reviews-outbox-publisher
auth-db
reviews-db
redis
mongo1
mongo2
mongo3
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

| Component | Port |
|---|---|
| Frontend | 8501 |
| API Gateway | 8000 |
| Auth Service 1 | 8001 |
| Auth Service 2 | 8002 |
| Catalog Service | 8003 |
| Reviews Service | 8004 |
| Feed API | 8005 |
| Config Server | 8010 |
| Neo4j Browser | 7474 |
| Neo4j Bolt | 7687 |
| Redis | 6379 |
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
