# Traceability Matrix

## 1. Purpose

This document maps project requirements to implementation components and verification scenarios.

## 2. Requirement Traceability

| Requirement | Implementation | Verification |
|---|---|---|
| Microservice architecture | Auth, Catalog, Reviews, Feed, API Gateway | `docker ps`, architecture diagram |
| API Gateway | `api-gateway` service | `GET /health`, UI requests |
| Authentication service | `auth-service` | Register, login, verify, logout |
| Login/logout | Auth endpoints | UI Auth page, API tests |
| Password hashing | bcrypt in Auth Service | User stored with password hash |
| JWT token | Auth Service | Login returns access token |
| Token/session storage | Redis | Verify token after service restart |
| Auth failover | `auth-service-1`, `auth-service-2` | Stop service 1, verify through service 2 |
| Separate DB per service | PostgreSQL, MongoDB, Neo4j | Docker Compose and service configs |
| NoSQL replication | MongoDB Replica Set + `mongo-init` bootstrap service | `docker exec mongo1 mongosh --eval "rs.status()..."` |
| Movie catalog | Catalog Service | Catalog UI and API |
| Review storage | Reviews Service + PostgreSQL | Create review, get reviews |
| Message queue | Kafka | `review.created` topic |
| Async event processing | Reviews producer + Feed consumer | Service logs |
| Social graph | Feed Service + Neo4j | Neo4j Browser graph |
| Follow users | Feed Service | Follow in UI |
| Personalized feed | Feed Service | Feed UI |
| UI | Streamlit frontend | Browser test |
| Demo data | Seed Demo World | UI data seeding |
| Docker deployment | docker-compose.yml (healthchecks on all data stores) | `docker compose up -d --build` |
| Three-layer architecture | api.py, service.py, repository.py | Repository structure |
| Continuous Integration | `.github/workflows/ci.yml` | GitHub Actions: compose lint, Python compile, multi-service image build |

## 3. Functional Requirement Mapping

### FR-1: User Registration

Implementation:

- Auth Service
- PostgreSQL
- `/auth/register`

Verification:

- Register user from UI
- Register user through API
- Check user appears in `/auth/users`

### FR-2: User Login

Implementation:

- Auth Service
- JWT
- Redis
- `/auth/login`

Verification:

- Login from UI
- Login through API
- Token returned

### FR-3: User Logout

Implementation:

- Auth Service
- Redis token deletion
- `/auth/logout`

Verification:

- Logout from UI
- Verify same token fails after logout

### FR-4: Token Verification

Implementation:

- Auth Service
- JWT validation
- Redis token lookup
- `/auth/verify`

Verification:

- Profile page Verify token
- API verify request

### FR-5: Movie Catalog

Implementation:

- Catalog Service
- MongoDB Replica Set
- `/catalog`

Verification:

- Catalog UI
- API get catalog
- MongoDB document check

### FR-6: Movie Search

Implementation:

- Catalog Service
- MongoDB query
- `/catalog/search`

Verification:

- Search by title
- Search by genre
- Search by year

### FR-7: Review Creation

Implementation:

- Reviews Service
- PostgreSQL
- `/reviews`

Verification:

- Write review from UI
- API create review
- Review appears in all reviews

### FR-8: Kafka Event Publishing

Implementation:

- Reviews Service Kafka producer
- Topic `review.created`

Verification:

- Reviews Service logs
- Kafka topic list

### FR-9: Kafka Event Consumption

Implementation:

- Feed Service Kafka consumer
- Neo4j update

Verification:

- Feed Service logs
- Neo4j graph query

### FR-10: Follow User

Implementation:

- Feed Service
- Neo4j `FOLLOWS`

Verification:

- Follow from UI
- Neo4j graph shows relationship

### FR-11: Personalized Feed

Implementation:

- Feed Service
- Neo4j query
- `/feed`

Verification:

- Follow user
- Create review by followed user
- Feed shows review

### FR-12: Demo Data Seeding

Implementation:

- Frontend Seed Demo World
- Auth, Catalog, Reviews, Feed APIs

Verification:

- Click Seed Demo World
- Users, movies, reviews, follows are created

## 4. Non-Functional Requirement Mapping

### NFR-1: Microservice Architecture

Implementation:

- Separate services in Docker Compose

Verification:

```powershell
docker ps
```

### NFR-2: Database-per-service

Implementation:

- Auth: PostgreSQL + Redis
- Catalog: MongoDB
- Reviews: PostgreSQL
- Feed: Neo4j

Verification:

- docker-compose.yml
- Service environment variables

### NFR-3: Auth Failover

Implementation:

- Two Auth instances
- Shared Redis token storage

Verification:

```powershell
docker stop auth-service-1
```

Then verify token through:

```text
http://localhost:8002/verify
```

### NFR-4: NoSQL Replication

Implementation:

- MongoDB Replica Set

Verification:

```javascript
rs.status().members.map(m => ({ name: m.name, state: m.stateStr }))
```

### NFR-5: Message Queue

Implementation:

- Kafka
- Topic `review.created`

Verification:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list
```

### NFR-6: Docker Deployment

Implementation:

- docker-compose.yml

Verification:

```powershell
docker compose up -d --build
```

### NFR-7: Three-Layer Architecture

Implementation:

Each backend service contains:

```text
api.py
service.py
repository.py
models.py
main.py
```

Verification:

- Repository structure
- Code review

## 5. End-to-End Trace

```text
User logs in
  ↓
User opens Catalog
  ↓
User selects movie
  ↓
User writes review
  ↓
Reviews Service stores review
  ↓
Reviews Service publishes Kafka event
  ↓
Feed Service consumes event
  ↓
Neo4j graph is updated
  ↓
Another user follows author
  ↓
Feed returns review
  ↓
UI displays review with username and movie title
```

## 6. Final Validation Checklist

| Check | Status |
|---|---|
| Docker Compose starts all services | Passed |
| API Gateway works | Passed |
| Auth works | Passed |
| Logout works | Passed |
| Redis token storage works | Passed |
| Auth failover works | Passed |
| Catalog works | Passed |
| MongoDB Replica Set works | Passed |
| Reviews work | Passed |
| Kafka producer works | Passed |
| Kafka consumer works | Passed |
| Feed works | Passed |
| Neo4j graph works | Passed |
| UI works | Passed |
| Demo data seeding works | Passed |
