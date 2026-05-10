# System Architecture

## 1. Overview

Movie Review Platform is a microservice-based web application for reviewing movies and following user activity. Users can register, log in, browse a movie catalog, write reviews, follow other users, and view a personalized social feed.

The system is built using independent microservices. Each microservice has its own data storage and follows a three-layer architecture:

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
        +------------------------+-------------------------+----------------------+
        |                        |                         |                      |
        v                        v                         v                      v
Auth Service              Catalog Service           Reviews Service        Feed Service
PostgreSQL + Redis        MongoDB Replica Set       PostgreSQL + Kafka     Neo4j + Kafka
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
- Route `/feed/*` requests to Feed Service
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
| `/feed` | Feed Service `/feed` |

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

The Reviews Service stores movie reviews and publishes review events.

Responsibilities:

- Create review
- Store review in PostgreSQL
- Get all reviews
- Get reviews by movie
- Get reviews by user
- Publish `review.created` events to Kafka

Storage:

```text
PostgreSQL
```

Message broker:

```text
Kafka
```

Kafka topic:

```text
review.created
```

---

## 3.6 Feed Service

The Feed Service handles social functionality.

Responsibilities:

- Create follow relationships
- Consume `review.created` events from Kafka
- Store graph relationships in Neo4j
- Return personalized user feed
- Return basic recommendations

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

Kafka is used for asynchronous communication between Reviews Service and Feed Service.

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
Feed Service
```

Purpose:

- Decouple review creation from feed update
- Allow Reviews Service to work without directly calling Feed Service
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
| Feed Service | Neo4j | Social graph |

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
Reviews Service -> Kafka -> Feed Service
```

Flow:

```text
1. User creates review.
2. Reviews Service stores review in PostgreSQL.
3. Reviews Service publishes review.created event to Kafka.
4. Feed Service consumes the event.
5. Feed Service updates Neo4j graph.
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
1. User logs in through auth-service-1.
2. Token id is stored in Redis.
3. auth-service-1 is stopped.
4. User verifies the same token through auth-service-2.
5. auth-service-2 validates token using Redis.
```

---

## 6.2 MongoDB Replica Set

The Catalog Service uses MongoDB Replica Set.

Benefits:

- Data replication
- Primary-secondary architecture
- Automatic primary election when quorum is available
- Improved fault tolerance for catalog data

Replica set check:

```javascript
rs.status().members.map(m => ({ name: m.name, state: m.stateStr }))
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
feed-service
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
| Feed Service | 8005 |
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