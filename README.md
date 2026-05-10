# Movie Review Platform

Microservice-based movie review platform built for the APZ project.

The system allows users to register, log in, browse a movie catalog, write reviews, follow other users, and view a personalized social feed. The project demonstrates microservice architecture, API Gateway, database-per-service pattern, JWT authentication, Redis-based token/session storage, MongoDB Replica Set, Kafka asynchronous messaging, Neo4j graph storage, and Docker Compose deployment.

---

## Features

- User registration and login
- JWT authentication
- Logout with token invalidation
- Redis storage for active JWT token identifiers
- Two Auth Service instances for failover demonstration
- Movie catalog with search by title, genre, and year
- Movie reviews with rating from 1 to 10
- Kafka event publishing after review creation
- Kafka consumer in Feed Service
- Social graph in Neo4j
- Follow users by username
- Personalized feed with reviews from followed users
- Demo data seeding from UI
- Streamlit web interface
- Docker Compose deployment

---

## Architecture

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

## Services

| Service | Description | Port |
|---|---|---|
| Frontend | Streamlit UI | 8501 |
| API Gateway | Single entry point for the frontend | 8000 |
| Auth Service 1 | Authentication service instance 1 | 8001 |
| Auth Service 2 | Authentication service instance 2 | 8002 |
| Catalog Service | Movie catalog service | 8003 |
| Reviews Service | Movie reviews service | 8004 |
| Feed Service | Social feed service | 8005 |
| Neo4j Browser | Graph database UI | 7474 |
| Kafka | Message broker | 9092 |
| Redis | Token storage | 6379 |
| MongoDB node 1 | MongoDB replica set node | 27017 |
| MongoDB node 2 | MongoDB replica set node | 27018 |
| MongoDB node 3 | MongoDB replica set node | 27019 |
| Auth PostgreSQL | Auth database | 5433 |
| Reviews PostgreSQL | Reviews database | 5434 |

---

## Databases and Infrastructure

| Component | Used for |
|---|---|
| PostgreSQL | Auth users and reviews |
| Redis | Active JWT token identifiers |
| MongoDB Replica Set | Movie catalog |
| Kafka | Asynchronous `review.created` events |
| Neo4j | Social graph, follows, reviewed movies |
| Docker Compose | Local deployment |

---

## Project Structure

```text
apz_project/
│
├── api-gateway/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── auth-service/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── catalog-service/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── reviews-service/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── feed-service/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/
│   ├── api-spec.md
│   ├── architecture.md
│   ├── backlog.md
│   └── use-cases.md
│
├── docker-compose.yml
└── README.md
```

Each microservice follows a three-layer structure:

```text
API layer
Service layer
Repository layer
```

---

## Prerequisites

Before running the project, install:

- Docker Desktop
- Git
- Web browser

No local Python environment is required because all services run inside Docker containers.

---

## How to Run

From the project root:

```powershell
cd C:\Users\user\Desktop\apz_project
```

Build and start all containers:

```powershell
docker compose up -d --build
```

Check running containers:

```powershell
docker ps
```

Expected main containers:

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

---

## Initialize MongoDB Replica Set

After the first startup, initialize MongoDB Replica Set.

Open Mongo shell:

```powershell
docker exec -it mongo1 mongosh
```

Run:

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

Wait 10–20 seconds and check status:

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

Exit:

```javascript
exit
```

Restart Catalog Service if needed:

```powershell
docker restart catalog-service
```

---

## Application URLs

Frontend UI:

```text
http://localhost:8501
```

API Gateway:

```text
http://localhost:8000
```

Neo4j Browser:

```text
http://localhost:7474
```

Neo4j credentials:

```text
username: neo4j
password: password123
```

---

## Health Checks

Check API Gateway:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Check all services through API Gateway:

```powershell
Invoke-RestMethod http://localhost:8000/auth/health
Invoke-RestMethod http://localhost:8000/catalog/health
Invoke-RestMethod http://localhost:8000/reviews/health
Invoke-RestMethod http://localhost:8000/feed/health
```

Expected response example:

```json
{
  "status": "ok",
  "service": "auth-service",
  "instance": "auth-service-1"
}
```

---

## Using the UI

Open:

```text
http://localhost:8501
```

Recommended demo flow:

1. Register a new user or log in.
2. Open `Catalog`.
3. Click `Seed Demo World`.
4. Check that movies appear in the catalog.
5. Open any movie and click `Write review` or `Read reviews`.
6. Create a review.
7. Open `Users` and check demo users.
8. Open `Feed`.
9. Follow another user by username.
10. Check `My feed`.
11. Open reviews for a movie directly from the feed.
12. Open `System` and check that services are healthy.

---

## Demo Data

The frontend includes a `Seed Demo World` button.

It creates:

- Demo users
- Demo movies
- Demo reviews
- Follow relationships
- Kafka events
- Neo4j graph data

This makes the system non-empty and ready for demonstration.

---

## API Examples

### Register

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/auth/register `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","username":"testuser","password":"123456"}'
```

### Login

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"123456"}'

$token = $login.access_token
```

### Verify token

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://localhost:8000/auth/verify `
  -Headers @{Authorization = "Bearer $token"}
```

### Create movie

```powershell
$movie = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/catalog `
  -ContentType "application/json" `
  -Body '{
    "title": "Interstellar",
    "description": "A science fiction film about space, time, and human survival.",
    "genres": ["Sci-Fi", "Drama"],
    "year": 2014,
    "director": "Christopher Nolan",
    "poster_url": "https://example.com/interstellar.jpg"
  }'

$movieId = $movie.id
```

### Create review

```powershell
$reviewBody = @{
  user_id = 1
  item_id = $movieId
  text = "Amazing movie with strong emotional and scientific themes."
  rating = 10
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/reviews `
  -ContentType "application/json" `
  -Body $reviewBody
```

### Follow user

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/feed/follow/2?follower_id=1"
```

### Get feed

```powershell
Invoke-RestMethod "http://localhost:8000/feed?user_id=1"
```

---

## Kafka Event Flow

When a review is created:

```text
Reviews Service
        |
        v
Kafka topic: review.created
        |
        v
Feed Service
        |
        v
Neo4j graph update
```

Check Reviews Service logs:

```powershell
docker logs reviews-service --tail 100
```

Expected log:

```text
[REVIEWS] Published event to Kafka
```

Check Feed Service logs:

```powershell
docker logs feed-service --tail 100
```

Expected log:

```text
[FEED] Consumed review.created event
```

List Kafka topics:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list
```

Expected topic:

```text
review.created
```

---

## Neo4j Graph Check

Open:

```text
http://localhost:7474
```

Run:

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50;
```

Expected nodes:

```text
User
Review
Item
```

Expected relationships:

```text
FOLLOWS
WROTE
ABOUT
REVIEWED
```

---

## Auth Failover Demo

The system has two Auth Service instances:

```text
auth-service-1
auth-service-2
```

Login through `auth-service-1`:

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8001/login `
  -ContentType "application/json" `
  -Body '{"email":"test@example.com","password":"123456"}'

$token = $login.access_token
```

Verify through `auth-service-1`:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://localhost:8001/verify `
  -Headers @{Authorization = "Bearer $token"}
```

Stop the first instance:

```powershell
docker stop auth-service-1
```

Verify the same token through `auth-service-2`:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://localhost:8002/verify `
  -Headers @{Authorization = "Bearer $token"}
```

Expected result:

```json
{
  "valid": true,
  "user_id": 1,
  "email": "test@example.com",
  "instance": "auth-service-2"
}
```

Start the first instance again:

```powershell
docker start auth-service-1
```

This demonstrates that active token state is stored in Redis and not in local service memory.

---

## Stopping the Project

Stop containers without deleting data:

```powershell
docker compose down
```

Start again:

```powershell
docker compose up -d
```

Stop containers and delete volumes:

```powershell
docker compose down -v
```

Warning: `-v` deletes database data. After using `-v`, MongoDB Replica Set must be initialized again.

---

## Rebuilding After Code Changes

Rebuild all services:

```powershell
docker compose up -d --build
```

Rebuild only frontend:

```powershell
docker compose build --no-cache frontend
docker compose up -d frontend
docker restart frontend
```

Rebuild only API Gateway:

```powershell
docker compose build --no-cache api-gateway
docker compose up -d api-gateway
```

Rebuild only one backend service:

```powershell
docker compose build --no-cache reviews-service
docker compose up -d reviews-service
```

---

## Documentation

Additional documentation is located in the `docs/` folder:

```text
docs/api-spec.md
docs/architecture.md
docs/backlog.md
docs/use-cases.md
```

---

## Implemented Requirements

| Requirement | Implementation |
|---|---|
| Microservice architecture | Auth, Catalog, Reviews, Feed, API Gateway |
| Authentication microservice | Auth Service |
| Login/logout | Implemented |
| Password hash | bcrypt hash in PostgreSQL |
| JWT/session | JWT |
| Distributed session/token storage | Redis |
| Duplicated application server | Two Auth Service instances |
| Separate database per service | PostgreSQL, MongoDB, Neo4j |
| NoSQL replication | MongoDB Replica Set |
| Message queue | Kafka |
| Async processing | Reviews Service to Kafka to Feed Service |
| API Gateway | Implemented |
| Docker Compose | Implemented |
| Working UI | Streamlit frontend |
| Documentation | Implemented |

---

## Technologies

- Python
- FastAPI
- Streamlit
- PostgreSQL
- Redis
- MongoDB
- Kafka
- Zookeeper
- Neo4j
- Docker
- Docker Compose