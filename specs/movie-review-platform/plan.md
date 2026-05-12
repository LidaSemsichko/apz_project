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
| Token storage | Redis |
| Message queue | Kafka |
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
- Redis for active token ids

Endpoints:

- `/register`
- `/login`
- `/logout`
- `/verify`
- `/me`
- `/users`
- `/users/by-username/{username}`

Failover:

- Two instances
- Shared Redis token storage
- Shared PostgreSQL database

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

## 3.4 Reviews Service

Purpose:

- Store reviews
- Publish review events

Storage:

- PostgreSQL

Messaging:

- Kafka producer

Endpoints:

- `/reviews`
- `/reviews/item/{item_id}`
- `/reviews/user/{user_id}`

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

### Auth Service

Two Auth instances are deployed:

```text
auth-service-1
auth-service-2
```

Both use:

- Same PostgreSQL database
- Same Redis storage

This allows token verification to continue if one instance fails.

### MongoDB

Catalog Service uses MongoDB Replica Set with three nodes:

```text
mongo1
mongo2
mongo3
```

Expected state:

```text
one PRIMARY
two SECONDARY
```

## 7. Implementation Steps

1. Create Docker Compose infrastructure
2. Implement Auth Service
3. Add Redis token storage
4. Add second Auth instance
5. Implement Catalog Service
6. Configure MongoDB Replica Set
7. Implement Reviews Service
8. Add Kafka producer
9. Implement Feed Service
10. Add Kafka consumer
11. Add Neo4j graph model
12. Implement API Gateway
13. Implement Streamlit UI
14. Add demo data seeding
15. Add documentation
16. Test all demo scenarios

## 8. Validation Plan

The implementation is valid if:

- All containers start
- Health endpoints return ok
- User can register and log in
- Logout invalidates token
- Auth failover works
- Movies can be created and searched
- Reviews can be created
- Kafka receives review events
- Feed consumes review events
- Neo4j graph contains relationships
- UI can demonstrate full flow
