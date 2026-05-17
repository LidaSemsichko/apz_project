# Specification: Movie Review Platform

## 1. Feature Name

Movie Review Platform

## 2. Problem Statement

Users need a platform where they can register, log in, browse movies, write reviews, follow other users, and view a personalized feed of reviews.

The system must also demonstrate distributed system concepts required by the course project:

- Microservice architecture
- Authentication microservice
- Database-per-service pattern
- Redis-based shared token/session state
- NoSQL replication
- Message queue
- Asynchronous processing
- API Gateway
- Docker Compose deployment

## 3. Goals

The system must:

- Allow users to register and log in
- Store passwords as hashes
- Use JWT tokens for authentication
- Store active token identifiers in Redis (replicated, HA via Sentinel)
- Support logout by removing token identifiers
- Run every stateless application tier (Auth, Catalog, Reviews, Feed API, Feed Consumer) as two instances behind the API Gateway so that the loss of a single instance does not interrupt service
- Provide a movie catalog
- Store movies in MongoDB Replica Set
- Allow users to create and read reviews
- Publish review creation events to Kafka via a transactional outbox
- Consume review events in Feed Service across two consumers sharing a single consumer group
- Store social graph in Neo4j
- Allow users to follow other users
- Return personalized feed
- Provide a browser UI
- Run locally through Docker Compose
- Keep credentials out of the committed repository (`.env` is git-ignored; `.env.example` is the committed template)

## 4. Non-Goals

The system does not aim to implement:

- Production-grade security hardening
- Real payment functionality
- Full admin panel
- Real external movie database integration
- Production monitoring
- Kubernetes deployment
- Advanced recommendation engine

## 5. Actors

## Guest

A user who is not authenticated.

Can:

- Register
- Log in

## Authenticated User

A user with valid JWT token.

Can:

- Browse catalog
- Search movies
- Write reviews
- Read reviews
- Follow users
- View feed
- View profile
- Log out

## Evaluator

A person who checks the project.

Can:

- Run the system
- Inspect UI
- Verify services
- Check MongoDB Replica Set
- Check Auth failover
- Check Kafka flow
- Check Neo4j graph

## System

Internal actor responsible for:

- Password hashing
- JWT generation
- Token validation
- Kafka event publishing
- Kafka event consumption
- Graph updates

## 6. Functional Requirements

### FR-1: User Registration

The system shall allow a guest to register using email, username, and password.

Acceptance criteria:

- Email is required
- Username is required
- Password is required
- Password is stored as hash
- User is saved in PostgreSQL
- Email must be unique
- Username must be unique

### FR-2: User Login

The system shall allow registered users to log in.

Acceptance criteria:

- User provides email and password
- Password is verified against stored hash
- JWT token is returned
- Token id is stored in Redis

### FR-3: User Logout

The system shall allow authenticated users to log out.

Acceptance criteria:

- Token id is removed from Redis
- Same JWT is no longer valid after logout

### FR-4: Token Verification

The system shall verify JWT tokens.

Acceptance criteria:

- JWT signature is validated
- Token id is checked in Redis
- Valid token returns user data
- Invalid token returns unauthorized response

### FR-5: User Lookup

The system shall return all users and find users by username.

Acceptance criteria:

- UI can display users by username
- Follow functionality can resolve username to user id

### FR-6: Movie Catalog

The system shall store and return movies.

Acceptance criteria:

- Movie has title, description, genres, year, director, poster_url
- Movie is stored in MongoDB Replica Set
- User can view all movies

### FR-7: Movie Search

The system shall allow movie search.

Acceptance criteria:

- Search by title works
- Search by genre works
- Search by year works

### FR-8: Review Creation

The system shall allow users to create reviews.

Acceptance criteria:

- Review contains user_id, item_id, text, rating
- Rating is between 1 and 10
- Review is stored in PostgreSQL

### FR-9: Review Event Publishing

The system shall publish an event after review creation.

Acceptance criteria:

- Event is published to Kafka topic `review.created`
- Event contains review_id, user_id, item_id, text, rating, created_at

### FR-10: Review Event Consumption

The system shall consume review events.

Acceptance criteria:

- Feed Service consumes `review.created`
- Neo4j graph is updated after event consumption

### FR-11: Follow User

The system shall allow users to follow other users.

Acceptance criteria:

- User can follow another user
- Relationship is stored in Neo4j

### FR-12: Personalized Feed

The system shall return reviews written by followed users.

Acceptance criteria:

- Feed contains reviews by followed users
- UI displays author username and movie title

### FR-13: Demo Data Seeding

The system shall provide demo data seeding.

Acceptance criteria:

- Demo users are created
- Demo movies are created
- Demo reviews are created
- Demo follow relationships are created
- Kafka events are produced through the normal Reviews Service flow
- Neo4j graph is updated through Feed Service consumer

## 7. Non-Functional Requirements

### NFR-1: Microservice Architecture

The system must be split into independent services.

### NFR-2: Database per Service

Each microservice must own its own database or storage.

### NFR-3: Horizontal Scaling and Fault Tolerance

Every stateless application tier must be deployed in at least two instances behind the API Gateway. The gateway must resolve instances through Config Server and retry the alternate instance on transport error or 5xx response, so that the loss of any single instance is invisible to the caller after one retry. This applies to:

- Auth Service (`auth-service-1`, `auth-service-2`)
- Catalog Service (`catalog-service-1`, `catalog-service-2`)
- Reviews Service (`reviews-service-1`, `reviews-service-2`)
- Feed API (`feed-api-1`, `feed-api-2`)
- Feed Consumer (`feed-consumer-1`, `feed-consumer-2`, same Kafka consumer group)

Stateful and coordinator-style components are scaled differently:

- MongoDB: 3-node replica set with automatic primary election.
- Redis: 1 master + 2 replicas + 3 sentinels (quorum = 2), failover automated by Sentinel.
- Reviews Outbox Publisher: two workers (`reviews-outbox-publisher-1`, `reviews-outbox-publisher-2`) coordinate through `FOR UPDATE SKIP LOCKED`, so they can publish in parallel without claiming the same pending row.

### NFR-4: NoSQL Replication

At least one NoSQL database must be replicated. Implemented via MongoDB Replica Set `rs0` (3 nodes).

### NFR-5: Cache / Session Store High Availability

The distributed token/session store (Redis) must survive the loss of its primary node without operator intervention. Implemented via Redis Sentinel (3-sentinel quorum) with one master and two replicas.

### NFR-6: Asynchronous Processing

At least one part of the system must use a message queue. The `review.created` topic uses 3 partitions so that the two Feed Consumer instances can process events in parallel and Kafka can rebalance partitions automatically when a consumer leaves or joins the group.

### NFR-7: Docker Deployment

The system must run with Docker Compose.

### NFR-8: Three-Layer Structure

Each microservice must use API, Service, and Repository layers.

### NFR-9: Secrets Hygiene

Credentials (JWT signing secret, both Postgres user/password pairs, Neo4j password) must not be hard-coded in `docker-compose.yml` or any committed file. They are referenced as `${VAR}` and substituted at compose-up time from a `.env` file. The repository ships a `.env.example` template; the real `.env` is git-ignored.

## 8. Main Flow

```text
User registers
  ↓
User logs in
  ↓
User opens Catalog
  ↓
User selects movie
  ↓
User writes review
  ↓
Review is stored in PostgreSQL
  ↓
Kafka event is published
  ↓
Feed Service consumes event
  ↓
Neo4j graph is updated
  ↓
Other users see review in feed
```

## 9. Success Criteria

The specification is implemented successfully if:

- UI works in browser
- User can register and log in
- Logout invalidates token
- Movies can be created and searched
- Reviews can be created and viewed
- Kafka events are published
- Feed Service consumes events
- Neo4j graph shows relationships
- MongoDB Replica Set works
- Auth failover works
- Docker Compose starts all services
