# API Specification

## 1. Overview

The Movie Review Platform exposes its functionality through an API Gateway. The API Gateway is the single external entry point for the frontend application and routes HTTP requests to internal microservices.

Local base URL:

```text
http://localhost:8000
```

Main services:

| Service | Responsibility |
|---|---|
| API Gateway | Routes requests to discovered service instances and provides enriched read endpoints |
| Auth Service | Registration, login, logout, JWT verification, user lookup |
| Catalog Service | Movie catalog and search |
| Reviews Service | Review creation and retrieval, PostgreSQL outbox |
| Reviews Outbox Publisher x2 | Two worker instances publish locked review events to Kafka |
| Feed API | Follow relationships, personal feed, Neo4j graph |
| Feed Consumer | Consumes Kafka review events into Neo4j |

---

## 2. API Gateway

### Health check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "api-gateway"
}
```

### Root endpoint

```http
GET /
```

### Enriched feed

```http
GET /feed/enriched
Authorization: Bearer <jwt-token>
```

Returns feed items enriched with `username` and `movie` data by composing Feed API, Auth Service, and Catalog Service responses.

### Enriched reviews

```http
GET /reviews/enriched
GET /reviews/enriched?item_id={movie_id}
Authorization: Bearer <jwt-token>
```

Returns review items enriched with `username` and `movie` data.

Response:

```json
{
  "message": "Movie Review Platform API Gateway is running",
  "routes": {
    "auth": "/auth",
    "catalog": "/catalog",
    "reviews": "/reviews",
    "feed": "/feed"
  }
}
```

---

# 3. Auth API

Base path:

```text
/auth
```

The Auth Service is responsible for user management and authentication. It stores users in PostgreSQL and active JWT token identifiers in Redis.

---

## 3.1 Register

```http
POST /auth/register
```

Request:

```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "123456"
}
```

Response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "instance": "auth-service-1"
}
```

Possible errors:

| Status | Description |
|---|---|
| 409 | Email already exists |
| 409 | Username already exists |
| 422 | Invalid request body |

---

## 3.2 Login

```http
POST /auth/login
```

Request:

```json
{
  "email": "user@example.com",
  "password": "123456"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@example.com",
  "instance": "auth-service-1"
}
```

Possible errors:

| Status | Description |
|---|---|
| 401 | Invalid email or password |

---

## 3.3 Verify token

```http
GET /auth/verify
```

Headers:

```http
Authorization: Bearer <jwt-token>
```

Response:

```json
{
  "valid": true,
  "user_id": 1,
  "email": "user@example.com",
  "instance": "auth-service-1"
}
```

Possible errors:

| Status | Description |
|---|---|
| 401 | Token is missing |
| 401 | Token is invalid |
| 401 | Token expired or logged out |

---

## 3.4 Get current user

```http
GET /auth/me
```

Headers:

```http
Authorization: Bearer <jwt-token>
```

Response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "instance": "auth-service-1"
}
```

---

## 3.5 Logout

```http
POST /auth/logout
```

Headers:

```http
Authorization: Bearer <jwt-token>
```

Response:

```json
{
  "message": "Logged out successfully",
  "instance": "auth-service-1"
}
```

After logout, the same JWT can no longer be verified because its token identifier is removed from Redis.

---

## 3.6 Get all users

```http
GET /auth/users
Authorization: Bearer <jwt-token>
```

Response:

```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "username": "username"
  }
]
```

---

## 3.7 Find user by username

```http
GET /auth/users/by-username/{username}
Authorization: Bearer <jwt-token>
```

Example:

```http
GET /auth/users/by-username/sasha
```

Response:

```json
{
  "id": 1,
  "email": "sasha@example.com",
  "username": "sasha"
}
```

---

## 3.8 Auth health check

```http
GET /auth/health
```

Response:

```json
{
  "status": "ok",
  "service": "auth-service",
  "instance": "auth-service-1",
  "dependencies": {
    "postgres": "ok",
    "redis": "ok",
    "redis_mode": "sentinel",
    "redis_master": "172.28.0.10:6379"
  }
}
```

Notes:

- `status` is derived from the actual dependency statuses (`postgres` and `redis`).
- `redis_mode` and `redis_master` are informational metadata about the active Redis connection mode and current master.

---

# 4. Catalog API

Base path:

```text
/catalog
```

The Catalog Service manages movies. Movie data is stored in MongoDB Replica Set. Catalog endpoints require `Authorization: Bearer <jwt-token>` except `/catalog/health`.

---

## 4.1 Create movie

```http
POST /catalog
```

Request:

```json
{
  "title": "Interstellar",
  "description": "A science fiction film about space, time, gravity, and human survival.",
  "genres": ["Sci-Fi", "Drama", "Adventure"],
  "year": 2014,
  "director": "Christopher Nolan",
  "poster_url": "https://example.com/interstellar.jpg"
}
```

Response:

```json
{
  "id": "movie-id",
  "title": "Interstellar",
  "description": "A science fiction film about space, time, gravity, and human survival.",
  "genres": ["Sci-Fi", "Drama", "Adventure"],
  "year": 2014,
  "director": "Christopher Nolan",
  "poster_url": "https://example.com/interstellar.jpg"
}
```

---

## 4.2 Get all movies

```http
GET /catalog
```

Response:

```json
[
  {
    "id": "movie-id",
    "title": "Interstellar",
    "description": "A science fiction film about space, time, gravity, and human survival.",
    "genres": ["Sci-Fi", "Drama", "Adventure"],
    "year": 2014,
    "director": "Christopher Nolan",
    "poster_url": "https://example.com/interstellar.jpg"
  }
]
```

---

## 4.3 Get movie by id

```http
GET /catalog/{movie_id}
```

Response:

```json
{
  "id": "movie-id",
  "title": "Interstellar",
  "description": "A science fiction film about space, time, gravity, and human survival.",
  "genres": ["Sci-Fi", "Drama", "Adventure"],
  "year": 2014,
  "director": "Christopher Nolan",
  "poster_url": "https://example.com/interstellar.jpg"
}
```

Possible errors:

| Status | Description |
|---|---|
| 404 | Movie not found |

---

## 4.4 Search movies

Search by title:

```http
GET /catalog/search?title=inter
```

Search by genre:

```http
GET /catalog/search?genre=Sci-Fi
```

Search by year:

```http
GET /catalog/search?year=2014
```

Combined search:

```http
GET /catalog/search?title=inter&genre=Sci-Fi&year=2014
```

Response:

```json
[
  {
    "id": "movie-id",
    "title": "Interstellar",
    "description": "A science fiction film about space, time, gravity, and human survival.",
    "genres": ["Sci-Fi", "Drama", "Adventure"],
    "year": 2014,
    "director": "Christopher Nolan",
    "poster_url": "https://example.com/interstellar.jpg"
  }
]
```

---

## 4.5 Catalog health check

```http
GET /catalog/health
```

Response:

```json
{
  "status": "ok",
  "service": "catalog-service"
}
```

---

# 5. Reviews API

Base path:

```text
/reviews
```

The Reviews Service stores reviews in PostgreSQL and writes `review.created` events to an outbox table in the same transaction. A pair of outbox publishers sends queued events to Kafka using Postgres row locking.

---

## 5.1 Create review

```http
POST /reviews
Authorization: Bearer <jwt-token>
```

Request:

```json
{
  "item_id": "movie-id",
  "text": "Great movie with strong atmosphere and story.",
  "rating": 9
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "item_id": "movie-id",
  "text": "Great movie with strong atmosphere and story.",
  "rating": 9,
  "created_at": "2026-05-10T13:05:03.411227"
}
```

Notes:

- `rating` must be between 1 and 10.
- The service uses the JWT user id.
- Review storage and outbox event creation are atomic.
- One of the outbox publishers later locks and publishes the queued Kafka event to topic `review.created`.

---

## 5.2 Get all reviews

```http
GET /reviews
Authorization: Bearer <jwt-token>
```

Response:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "item_id": "movie-id",
    "text": "Great movie with strong atmosphere and story.",
    "rating": 9,
    "created_at": "2026-05-10T13:05:03.411227"
  }
]
```

---

## 5.3 Get reviews by movie

```http
GET /reviews/item/{item_id}
Authorization: Bearer <jwt-token>
```

Response:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "item_id": "movie-id",
    "text": "Great movie with strong atmosphere and story.",
    "rating": 9,
    "created_at": "2026-05-10T13:05:03.411227"
  }
]
```

---

## 5.4 Get reviews by user

```http
GET /reviews/user/{user_id}
Authorization: Bearer <jwt-token>
```

Response:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "item_id": "movie-id",
    "text": "Great movie with strong atmosphere and story.",
    "rating": 9,
    "created_at": "2026-05-10T13:05:03.411227"
  }
]
```

---

## 5.5 Reviews health check

```http
GET /reviews/health
```

Response:

```json
{
  "status": "ok",
  "service": "reviews-service"
}
```

---

# 6. Feed API

Base path:

```text
/feed
```

The Feed API manages follow relationships and reads social graph data from Neo4j. The Feed Consumer consumes Kafka events and writes review graph data to Neo4j.

---

## 6.1 Follow user

```http
POST /feed/follow/{following_id}
Authorization: Bearer <jwt-token>
```

Example:

```http
POST /feed/follow/2
```

Response:

```json
{
  "message": "User followed successfully",
  "follower_id": 1,
  "following_id": 2
}
```

---

## 6.2 Get personal feed

```http
GET /feed
Authorization: Bearer <jwt-token>
```

Response:

```json
[
  {
    "review_id": 2,
    "user_id": 2,
    "item_id": "movie-id",
    "text": "A visually powerful movie with excellent storytelling.",
    "rating": 9,
    "created_at": "2026-05-10T13:10:06.167602"
  }
]
```

---

## 6.3 Get recommendations

```http
GET /feed/recommendations
Authorization: Bearer <jwt-token>
```

Response:

```json
[
  {
    "item_id": "movie-id",
    "score": 2
  }
]
```

---

## 6.4 Feed health check

```http
GET /feed/health
```

Response:

```json
{
  "status": "ok",
  "service": "feed-api"
}
```

---

# 7. Kafka Event Specification

## Topic

```text
review.created
```

## Producer

```text
Reviews Outbox Publisher x2
```

The publishers coordinate through `SELECT ... FOR UPDATE SKIP LOCKED`, so each worker locks a different pending row while it publishes to Kafka.

## Consumer

```text
Feed Consumer
```

## Event payload

```json
{
  "event_type": "review.created",
  "review_id": 1,
  "user_id": 1,
  "item_id": "movie-id",
  "text": "Great movie with strong atmosphere and story.",
  "rating": 9,
  "created_at": "2026-05-10T13:05:03.411227"
}
```

## Event flow

```text
User creates review
        |
        v
Reviews Service stores review and outbox event in PostgreSQL
        |
        v
One Reviews Outbox Publisher instance locks and publishes the review.created event to Kafka
        |
        v
Feed Consumer consumes event
        |
        v
Feed Consumer updates Neo4j graph and commits the Kafka offset
```
