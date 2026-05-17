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
| Token/session storage | Redis (Sentinel-managed: master + 2 replicas + 3 sentinels) | Verify token after Redis master failover (`docker stop redis-master`); `/auth/health` reports new `redis_master` within ~15s |
| Horizontal scaling | Two instances of every stateless tier (auth, catalog, reviews, feed-api, feed-consumer) behind gateway-side discovery + retry | `docker stop <any single instance>`, repeat request through gateway, observe no error |
| Cache HA via Sentinel | `redis-master`, `redis-replica-1/2`, `redis-sentinel-1/2/3` (quorum = 2) | `docker stop redis-master`, then `sentinel get-master-addr-by-name mymaster` reports a replica |
| Separate DB per service | PostgreSQL (auth-db, reviews-db), MongoDB, Neo4j | Docker Compose and service configs |
| NoSQL replication | MongoDB Replica Set + `mongo-init` bootstrap service | `docker exec mongo1 mongosh --eval "rs.status()..."` |
| Kafka consumer group | `feed-consumer-1` and `feed-consumer-2` in `feed-service-consumer-group`, 3 partitions | `kafka-consumer-groups --describe`, then `docker stop feed-consumer-1`, observe rebalance |
| Transactional outbox | Reviews-service writes review + outbox event in one Postgres TX; two publishers drain it with `FOR UPDATE SKIP LOCKED` | Inspect `outbox_events` rows + `reviews-outbox-publisher-{1,2}` logs |
| Secrets hygiene | `${VAR}` substitutions in `docker-compose.yml`; `.env.example` template committed; `.env` git-ignored | `grep` the compose file for literal credentials returns nothing; CI fails on unset `${VAR}` |
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

### NFR-3: Horizontal Scaling and Fault Tolerance

Implementation:

- Two instances per stateless tier: `auth-service-{1,2}`, `catalog-service-{1,2}`, `reviews-service-{1,2}`, `feed-api-{1,2}`, `feed-consumer-{1,2}`
- Gateway resolves instances via Config Server and retries the alternate instance on transport error or 5xx
- Reviews Outbox Publisher runs as `reviews-outbox-publisher-{1,2}` and coordinates through `FOR UPDATE SKIP LOCKED` (documented in `plan.md` Section 6.3)

Verification:

```powershell
docker stop auth-service-1
docker stop catalog-service-1
docker stop reviews-service-1
docker stop feed-api-1
docker stop feed-consumer-1
```

Then, through the gateway:

```text
http://localhost:8000/health
http://localhost:8000/<tier>/...
```

### NFR-3a: Cache HA via Sentinel

Implementation:

- `redis-master` + `redis-replica-1` + `redis-replica-2`
- `redis-sentinel-1/2/3` (quorum = 2, `down-after-milliseconds=5000`)
- Auth Service uses a shared Sentinel-aware Redis client helper from `common.redis_client`

Verification:

```powershell
docker stop redis-master
Start-Sleep -Seconds 15
docker exec redis-sentinel-1 redis-cli -p 26379 sentinel get-master-addr-by-name mymaster
# expect: redis-replica-1 or redis-replica-2

(Invoke-RestMethod http://localhost:8000/auth/health).dependencies.redis_master
# expect: the new master
```

### NFR-4: NoSQL Replication

Implementation:

- MongoDB Replica Set

Verification:

```javascript
rs.status().members.map(m => ({ name: m.name, state: m.stateStr }))
```

### NFR-5: Message Queue and Consumer Group Rebalancing

Implementation:

- Kafka
- Topic `review.created` with 3 partitions (`KAFKA_NUM_PARTITIONS=3`)
- Two consumers in `feed-service-consumer-group`

Verification:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list
docker exec -it kafka kafka-consumer-groups --bootstrap-server kafka:9092 `
  --group feed-service-consumer-group --describe
# expect: 3 partitions split across feed-consumer-1 and feed-consumer-2

docker stop feed-consumer-1
Start-Sleep -Seconds 10
docker exec -it kafka kafka-consumer-groups --bootstrap-server kafka:9092 `
  --group feed-service-consumer-group --describe
# expect: all 3 partitions on feed-consumer-2
```

### NFR-6: Docker Deployment

Implementation:

- docker-compose.yml

Verification:

```powershell
docker compose up -d --build
```

### NFR-7: Secrets Hygiene

Implementation:

- `docker-compose.yml` references credentials as `${VAR}`
- `.env.example` committed; `.env` git-ignored
- CI provisions `.env` from `.env.example` and fails on any unset `${VAR}`

Verification:

```powershell
Select-String -Path docker-compose.yml -Pattern "supersecret|password123|auth_pass|reviews_pass"
# expect: no matches

Get-Content .gitignore | Select-String "^.env$"
# expect: .env is listed
```

### NFR-8: Three-Layer Architecture

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
| Docker Compose starts all 28 long-running services + `mongo-init` exits 0 | Passed |
| API Gateway works | Passed |
| Auth works | Passed |
| Logout works | Passed |
| Redis token storage works | Passed |
| Auth failover works (stop `auth-service-1`, traffic continues) | Passed |
| Catalog failover works (stop `catalog-service-1`, traffic continues) | Passed |
| Reviews failover works (stop `reviews-service-1`, traffic continues) | Passed |
| Feed API failover works (stop `feed-api-1`, traffic continues) | Passed |
| Feed Consumer rebalances on failure (stop `feed-consumer-1`, partitions reassigned) | Passed |
| Redis Sentinel failover works (stop `redis-master`, replica promoted) | Passed |
| MongoDB Replica Set works | Passed |
| Reviews work | Passed |
| Outbox publisher delivers to Kafka | Passed |
| Kafka producer works | Passed |
| Kafka consumer works | Passed |
| Feed works | Passed |
| Neo4j graph works | Passed |
| UI works | Passed |
| Demo data seeding works | Passed |
| No literal credentials in `docker-compose.yml` (all `${VAR}`) | Passed |
| CI provisions `.env` from `.env.example` and fails on unset `${VAR}` | Passed |
