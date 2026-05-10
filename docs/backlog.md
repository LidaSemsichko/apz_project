# Product Backlog

## 1. Project Goal

The goal of the project is to build a microservice-based movie review platform where users can register, log in, browse movies, write reviews, follow other users, and view a personalized activity feed.

The project demonstrates:

- Microservice architecture
- API Gateway
- Authentication service
- Database-per-service pattern
- Redis-based token storage
- Service failover
- MongoDB Replica Set
- Kafka asynchronous messaging
- Neo4j graph database
- Docker Compose deployment
- Web UI

---

# 2. Epics

## Epic 1: Authentication and User Management

Users must be able to create accounts, log in, log out, and use the system through JWT authentication.

### US-1.1: User registration

As a guest, I want to create an account using email, username, and password so that I can use the platform.

Acceptance criteria:

- User can submit email, username, and password
- Email must be unique
- Username must be unique
- Password is stored as hash
- User is stored in PostgreSQL

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-1.2: User login

As a registered user, I want to log in with email and password so that I can access the system.

Acceptance criteria:

- User submits email and password
- Auth Service verifies password hash
- Auth Service returns JWT token
- Token id is stored in Redis
- Frontend stores token for the session

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-1.3: User logout

As an authenticated user, I want to log out so that my session becomes invalid.

Acceptance criteria:

- User sends logout request with JWT token
- Auth Service removes token id from Redis
- Same token can no longer be verified

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-1.4: Token verification

As a frontend application, I want to verify the current token so that I can check whether the user is authenticated.

Acceptance criteria:

- Token is sent in Authorization header
- Auth Service validates JWT
- Auth Service checks token id in Redis
- Valid token returns user information
- Invalid token returns unauthorized response

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-1.5: User lookup by username

As a user, I want to find other users by username so that I can follow them.

Acceptance criteria:

- System can return all users
- System can return user by username
- UI displays usernames instead of only ids

Priority:

```text
Should have
```

Status:

```text
Implemented
```

---

## Epic 2: Movie Catalog

Users must be able to browse and search movies.

### US-2.1: Add movie

As an administrator or demo user, I want to add movies to the catalog so that users can review them.

Acceptance criteria:

- Movie has title, description, genres, year, director, poster URL
- Movie is stored in MongoDB
- Movie receives unique id

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-2.2: Browse catalog

As an authenticated user, I want to browse movies so that I can choose a movie to review.

Acceptance criteria:

- UI displays movie cards
- Movie card shows title, year, description, director, genres
- User can select movie for reviews

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-2.3: Search movies

As an authenticated user, I want to search movies by title or genre so that I can find movies faster.

Acceptance criteria:

- Search by title works
- Search by genre works
- Search results are displayed as movie cards

Priority:

```text
Should have
```

Status:

```text
Implemented
```

---

### US-2.4: Seed demo movies

As an evaluator, I want to quickly populate the catalog with demo movies so that the system is not empty during demonstration.

Acceptance criteria:

- UI has Seed Demo World button
- Demo movies are created only if they do not already exist
- Existing movies are skipped

Priority:

```text
Should have
```

Status:

```text
Implemented
```

---

## Epic 3: Reviews

Users must be able to write and read movie reviews.

### US-3.1: Write review

As an authenticated user, I want to write a review for a selected movie so that I can share my opinion.

Acceptance criteria:

- User selects movie
- User writes review text
- User selects rating from 1 to 10
- Review is stored in PostgreSQL
- Review is linked to user id and movie id

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-3.2: Publish review event

As the system, I want to publish an event when a review is created so that the Feed Service can update asynchronously.

Acceptance criteria:

- Reviews Service publishes `review.created` event
- Event is sent to Kafka
- Event contains review id, user id, movie id, text, rating, timestamp

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-3.3: Read all reviews

As a user, I want to see all reviews so that I can explore activity on the platform.

Acceptance criteria:

- Reviews Service returns all reviews
- UI displays author username
- UI displays movie title
- UI displays rating and text

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-3.4: Read reviews for selected movie

As a user, I want to read reviews for one movie so that I can understand opinions about that movie.

Acceptance criteria:

- User can open reviews for a movie from Catalog
- User can open reviews for a movie from Feed
- UI displays only reviews for selected movie

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

## Epic 4: Social Feed

Users must be able to follow others and view activity from followed users.

### US-4.1: Follow user

As an authenticated user, I want to follow another user by username so that I can see their reviews in my feed.

Acceptance criteria:

- UI displays users by username
- User can follow another user
- Feed Service creates `FOLLOWS` relationship in Neo4j

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-4.2: Consume review events

As the Feed Service, I want to consume review events from Kafka so that I can update the graph database.

Acceptance criteria:

- Feed Service connects to Kafka
- Feed Service consumes `review.created`
- Feed Service stores graph data in Neo4j

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-4.3: Personalized feed

As a user, I want to view reviews written by users I follow so that I can see relevant activity.

Acceptance criteria:

- Feed Service returns reviews by followed users
- UI displays username
- UI displays movie title
- UI displays button to open movie reviews

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-4.4: Basic recommendations

As a user, I want basic movie recommendations based on graph relationships so that I can discover new movies.

Acceptance criteria:

- Feed Service queries Neo4j
- Recommendations are based on reviewed items
- Response contains item id and score

Priority:

```text
Could have
```

Status:

```text
Implemented
```

---

## Epic 5: Infrastructure and Fault Tolerance

The system must demonstrate distributed architecture concepts.

### US-5.1: Docker Compose deployment

As a developer, I want to run the whole system with Docker Compose so that setup is simple.

Acceptance criteria:

- All services are in docker-compose.yml
- Frontend runs on port 8501
- API Gateway runs on port 8000
- Databases and infrastructure services start together

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-5.2: MongoDB Replica Set

As a system owner, I want Catalog Service to use MongoDB Replica Set so that catalog data is replicated.

Acceptance criteria:

- Three MongoDB nodes are running
- Replica set is initialized as `rs0`
- One node is primary
- Two nodes are secondary

Priority:

```text
Must have
```

Status:

```text
Implemented
```

---

### US-5.3: Auth Service failover

As a system owner, I want authentication to remain available after one Auth instance fails.

Acceptance criteria:

- Two Auth Service instances exist
- Token is stored in Redis
- User logs in through one instance
- The other instance can verify the same token after the first one is stopped

Priority:

```text
Must have
```

Status:

```text
Implemented and tested
```

---

### US-5.4: Kafka asynchronous processing

As a system owner, I want review processing to use message queue so that Reviews Service is decoupled from Feed Service.

Acceptance criteria:

- Reviews Service publishes events
- Feed Service consumes events
- Neo4j graph is updated after event consumption

Priority:

```text
Must have
```

Status:

```text
Implemented and tested
```

---

## Epic 6: User Interface

The platform should be usable from a browser.

### US-6.1: Login gate

As a user, I should not access the platform before logging in.

Acceptance criteria:

- UI shows login/register screen for unauthenticated users
- Main pages are hidden until login
- Logout clears session

Priority:

```text
Should have
```

Status:

```text
Implemented
```

---

### US-6.2: Demo data seeding

As an evaluator, I want one button to populate the system with demo data so that the project can be demonstrated quickly.

Acceptance criteria:

- Seed Demo World creates users
- Seed Demo World creates movies
- Seed Demo World creates reviews
- Seed Demo World creates follows
- Kafka and Neo4j are updated through normal system flow

Priority:

```text
Should have
```

Status:

```text
Implemented
```

---

# 3. Priority Summary

## Must have

- Microservice architecture
- Authentication service
- Login/logout
- JWT token verification
- Password hashing
- Redis token storage
- Separate databases for services
- MongoDB Replica Set
- Kafka message queue
- Asynchronous Reviews-to-Feed processing
- API Gateway
- Docker Compose deployment
- Working system

## Should have

- Streamlit UI
- Demo data seeding
- Username-based follow
- Movie titles in reviews and feed
- System health dashboard
- Neo4j graph visualization

## Could have

- Advanced recommendations
- Movie posters
- Review editing
- Review deletion
- User profile pages with activity history
- CI pipeline
- Kubernetes deployment

---

# 4. Current Status

| Feature | Status |
|---|---|
| API Gateway | Implemented |
| Auth Service | Implemented |
| Catalog Service | Implemented |
| Reviews Service | Implemented |
| Feed Service | Implemented |
| PostgreSQL for Auth | Implemented |
| PostgreSQL for Reviews | Implemented |
| Redis token storage | Implemented |
| MongoDB Replica Set | Implemented |
| Kafka producer | Implemented |
| Kafka consumer | Implemented |
| Neo4j graph | Implemented |
| Streamlit UI | Implemented |
| Demo data seeding | Implemented |
| Auth failover | Tested |
| End-to-end flow | Tested |