# Data Model

## 1. Overview

This document describes the data models used by the Movie Review Platform.

The system follows database-per-service design. Each microservice owns its own storage and does not share database tables with other services.

## 2. Auth Service Data Model

Storage:

```text
PostgreSQL
```

Table:

```text
users
```

Fields:

| Field | Type | Description |
|---|---|---|
| id | integer | Primary key |
| email | string | Unique user email |
| username | string | Unique username |
| password_hash | string | Hashed password |
| created_at | datetime | User creation timestamp |

Example:

```json
{
  "id": 1,
  "email": "sasha@example.com",
  "username": "sasha",
  "password_hash": "$2b$12$...",
  "created_at": "2026-05-10T13:00:00"
}
```

## 3. Redis Token Model

Storage:

```text
Redis
```

Redis stores active JWT token identifiers.

Key format:

```text
auth_token:{jti}
```

Value:

```text
user_id
```

Example:

```text
auth_token:1c1fc061-6beb-4f57-b229-86db2b7f75ec -> 1
```

TTL:

```text
3600 seconds
```

Purpose:

- Verify active sessions
- Invalidate tokens on logout
- Support Auth Service failover

## 4. Catalog Service Data Model

Storage:

```text
MongoDB Replica Set
```

Collection:

```text
movies
```

Fields:

| Field | Type | Description |
|---|---|---|
| _id | string | Movie id |
| title | string | Movie title |
| description | string | Movie description |
| genres | list[string] | Movie genres |
| year | integer | Release year |
| director | string | Director |
| poster_url | string | Poster URL |

Example:

```json
{
  "_id": "1642de6f-f7dc-4bdf-9722-94d012e569b7",
  "title": "Interstellar",
  "description": "A science fiction film about space, time, gravity, and human survival.",
  "genres": ["Sci-Fi", "Drama", "Adventure"],
  "year": 2014,
  "director": "Christopher Nolan",
  "poster_url": "https://example.com/interstellar.jpg"
}
```

## 5. Reviews Service Data Model

Storage:

```text
PostgreSQL
```

Table:

```text
reviews
```

Fields:

| Field | Type | Description |
|---|---|---|
| id | integer | Primary key |
| user_id | integer | Author user id |
| item_id | string | Movie id |
| text | string | Review text |
| rating | integer | Rating from 1 to 10 |
| created_at | datetime | Review creation timestamp |

Example:

```json
{
  "id": 1,
  "user_id": 1,
  "item_id": "1642de6f-f7dc-4bdf-9722-94d012e569b7",
  "text": "Amazing movie with strong atmosphere.",
  "rating": 10,
  "created_at": "2026-05-10T13:05:03.411227"
}
```

## 6. Feed Service Graph Model

Storage:

```text
Neo4j
```

Node labels:

| Label | Description |
|---|---|
| User | Platform user |
| Review | Movie review |
| Item | Movie |

Relationship types:

| Relationship | Direction | Description |
|---|---|---|
| FOLLOWS | User -> User | User follows another user |
| WROTE | User -> Review | User wrote a review |
| ABOUT | Review -> Item | Review is about a movie |
| REVIEWED | User -> Item | User reviewed a movie |

Graph example:

```text
(User {id: 1})-[:FOLLOWS]->(User {id: 2})
(User {id: 2})-[:WROTE]->(Review {id: 5})
(Review {id: 5})-[:ABOUT]->(Item {id: "movie-id"})
(User {id: 2})-[:REVIEWED]->(Item {id: "movie-id"})
```

## 7. Cross-Service References

The system does not use foreign keys across databases. References are stored as ids:

| Source | Reference |
|---|---|
| Review.user_id | Auth User.id |
| Review.item_id | Catalog Movie.id |
| Neo4j User.id | Auth User.id |
| Neo4j Item.id | Catalog Movie.id |
| Neo4j Review.id | Reviews Review.id |

This keeps services independent while allowing the frontend to resolve usernames and movie titles through API calls.
