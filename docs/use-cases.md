# Use Cases

## 1. Actors

## Guest

A guest is a user who has not logged in.

A guest can:

- Register
- Log in

## Authenticated User

An authenticated user has a valid JWT token.

An authenticated user can:

- Browse catalog
- Search movies
- Write reviews
- Read reviews
- Follow users
- View feed
- View users
- View profile
- Log out

## System

The system performs internal operations:

- Hash passwords
- Generate JWT tokens
- Store token identifiers in Redis
- Publish Kafka events
- Consume Kafka events
- Update Neo4j graph
- Query databases

## Evaluator

An evaluator checks whether the system satisfies project requirements.

An evaluator can:

- Run Docker Compose
- Open UI
- Check service health
- Verify MongoDB Replica Set
- Verify Auth failover
- Verify Kafka event flow
- View Neo4j graph

---

# UC-1: Register Account

## Primary actor

Guest

## Goal

Create a new user account.

## Preconditions

- User is not logged in
- Email is not registered
- Username is not registered

## Main flow

1. Guest opens the frontend.
2. Guest enters username, email, and password.
3. Frontend sends request to API Gateway.
4. API Gateway forwards request to Auth Service.
5. Auth Service checks email uniqueness.
6. Auth Service checks username uniqueness.
7. Auth Service hashes password.
8. Auth Service stores user in PostgreSQL.
9. System returns created user information.

## Alternative flow: email already exists

1. Auth Service detects existing email.
2. System returns conflict error.

## Alternative flow: username already exists

1. Auth Service detects existing username.
2. System returns conflict error.

## Result

User account is created.

---

# UC-2: Log In

## Primary actor

Guest

## Goal

Authenticate and access the platform.

## Preconditions

- User account exists

## Main flow

1. Guest enters email and password.
2. Frontend sends login request to API Gateway.
3. API Gateway forwards request to Auth Service.
4. Auth Service finds user by email.
5. Auth Service verifies password hash.
6. Auth Service creates JWT token.
7. Auth Service stores token id in Redis.
8. System returns JWT and user data.
9. Frontend stores token in UI session.

## Alternative flow: invalid credentials

1. Auth Service cannot verify credentials.
2. System returns unauthorized response.

## Result

User is authenticated.

---

# UC-3: Log Out

## Primary actor

Authenticated User

## Goal

End current session.

## Preconditions

- User is logged in
- User has valid JWT token

## Main flow

1. User clicks Logout.
2. Frontend sends logout request with JWT token.
3. API Gateway forwards request to Auth Service.
4. Auth Service extracts token id.
5. Auth Service removes token id from Redis.
6. Frontend clears local session.

## Result

User is logged out and token is invalidated.

---

# UC-4: Verify Token

## Primary actor

Frontend or Evaluator

## Goal

Check whether current user token is valid.

## Preconditions

- User has JWT token

## Main flow

1. Frontend sends request with Authorization header.
2. API Gateway forwards request to Auth Service.
3. Auth Service validates JWT signature.
4. Auth Service checks token id in Redis.
5. Auth Service returns token status and user data.

## Alternative flow: token was logged out

1. JWT is structurally valid.
2. Token id is missing in Redis.
3. Auth Service returns unauthorized response.

## Result

System confirms whether token is valid.

---

# UC-5: Browse Catalog

## Primary actor

Authenticated User

## Goal

View available movies.

## Preconditions

- User is logged in
- Catalog Service is running

## Main flow

1. User opens Catalog page.
2. Frontend sends request to API Gateway.
3. API Gateway forwards request to Catalog Service.
4. Catalog Service reads movies from MongoDB Replica Set.
5. Catalog Service returns movies.
6. UI displays movies as cards.

## Result

User sees movie catalog.

---

# UC-6: Search Movie

## Primary actor

Authenticated User

## Goal

Find movies by title or genre.

## Preconditions

- User is logged in
- Movies exist in catalog

## Main flow

1. User enters title or genre filter.
2. Frontend sends search request to API Gateway.
3. API Gateway forwards request to Catalog Service.
4. Catalog Service queries MongoDB.
5. System returns matching movies.
6. UI displays matching movie cards.

## Result

User finds relevant movies.

---

# UC-7: Seed Demo World

## Primary actor

Authenticated User or Evaluator

## Goal

Populate the system with demo users, movies, reviews, and follow relationships.

## Preconditions

- User is logged in
- All services are running

## Main flow

1. User opens Catalog page.
2. User clicks Seed Demo World.
3. Frontend creates demo users through Auth API.
4. Frontend creates demo movies through Catalog API.
5. Frontend creates demo reviews through Reviews API.
6. Reviews Service stores reviews in PostgreSQL.
7. Reviews Service publishes `review.created` events to Kafka.
8. Feed Service consumes events from Kafka.
9. Feed Service stores graph relationships in Neo4j.
10. Frontend creates demo follow relationships through Feed API.
11. UI displays seeding result.

## Result

The system contains realistic demo data.

---

# UC-8: Select Movie

## Primary actor

Authenticated User

## Goal

Choose a movie for reading or writing reviews.

## Preconditions

- User is logged in
- Movie exists in catalog

## Main flow

1. User opens Catalog page.
2. User chooses a movie card.
3. User clicks Write review or Read reviews.
4. Frontend stores selected movie.
5. Frontend opens Reviews page.

## Result

Selected movie is available on Reviews page.

---

# UC-9: Write Review

## Primary actor

Authenticated User

## Goal

Write a review for a movie.

## Preconditions

- User is logged in
- Movie is selected
- Reviews Service is running
- Kafka is running

## Main flow

1. User opens Reviews page.
2. User enters review text.
3. User selects rating.
4. Frontend sends review request to API Gateway.
5. API Gateway forwards request to Reviews Service.
6. Reviews Service stores review in PostgreSQL.
7. Reviews Service publishes `review.created` event to Kafka.
8. System returns created review.

## Result

Review is stored and event is published.

---

# UC-10: Read Reviews for Movie

## Primary actor

Authenticated User

## Goal

Read reviews for a selected movie.

## Preconditions

- User is logged in
- Movie exists

## Main flow

1. User opens Reviews page for selected movie.
2. Frontend requests reviews by movie id.
3. API Gateway forwards request to Reviews Service.
4. Reviews Service queries PostgreSQL.
5. System returns reviews for movie.
6. Frontend resolves usernames through Auth API.
7. Frontend displays review cards.

## Result

User sees reviews for selected movie.

---

# UC-11: Read All Reviews

## Primary actor

Authenticated User

## Goal

View all reviews in the system.

## Preconditions

- User is logged in

## Main flow

1. User opens All Reviews section.
2. Frontend requests all reviews.
3. Reviews Service returns reviews.
4. Frontend resolves usernames through Auth API.
5. Frontend resolves movie titles through Catalog API.
6. UI displays full review cards.

## Result

User can browse all review activity.

---

# UC-12: Follow User

## Primary actor

Authenticated User

## Goal

Follow another user.

## Preconditions

- User is logged in
- Another user exists

## Main flow

1. User opens Feed page.
2. User opens Follow People tab.
3. User selects another user by username.
4. Frontend resolves username to user id.
5. Frontend sends follow request to Feed Service through API Gateway.
6. Feed Service creates `FOLLOWS` relationship in Neo4j.

## Result

Current user follows selected user.

---

# UC-13: View Personal Feed

## Primary actor

Authenticated User

## Goal

View reviews written by followed users.

## Preconditions

- User is logged in
- User follows at least one other user
- Followed users have reviews

## Main flow

1. User opens Feed page.
2. Frontend requests feed for current user.
3. Feed Service queries Neo4j.
4. Feed Service returns reviews from followed users.
5. Frontend resolves usernames and movie titles.
6. UI displays feed cards.

## Result

User sees personalized social feed.

---

# UC-14: Open Movie Reviews from Feed

## Primary actor

Authenticated User

## Goal

Open all reviews for a movie directly from feed.

## Preconditions

- User is logged in
- Feed contains reviews
- Reviewed movie exists in Catalog

## Main flow

1. User views feed.
2. User sees review card with movie title.
3. User clicks Open reviews for movie.
4. Frontend stores selected movie.
5. Frontend opens Reviews page.
6. UI displays reviews for selected movie.

## Result

User navigates from feed item to movie-specific reviews.

---

# UC-15: Process Review Event

## Primary actor

System

## Goal

Update social graph after review creation.

## Preconditions

- Review was created
- Kafka is running
- Feed Service is running
- Neo4j is running

## Main flow

1. Reviews Service publishes `review.created` event.
2. Kafka stores event in topic.
3. Feed Service consumes event.
4. Feed Service creates or updates User node.
5. Feed Service creates or updates Item node.
6. Feed Service creates or updates Review node.
7. Feed Service creates graph relationships:
   - `(User)-[:WROTE]->(Review)`
   - `(Review)-[:ABOUT]->(Item)`
   - `(User)-[:REVIEWED]->(Item)`

## Result

Neo4j graph is updated asynchronously.

---

# UC-16: Verify Auth Failover

## Primary actor

Evaluator

## Goal

Demonstrate that authentication remains available after one Auth instance fails.

## Preconditions

- Both Auth Service instances are running
- Redis is running
- User is logged in

## Main flow

1. User logs in through `auth-service-1`.
2. Auth Service stores token id in Redis.
3. Evaluator stops `auth-service-1`.
4. Evaluator sends verify request to `auth-service-2`.
5. `auth-service-2` verifies same token using Redis.

## Result

Authentication works even after one Auth instance is stopped.

---

# UC-17: Verify MongoDB Replica Set

## Primary actor

Evaluator

## Goal

Demonstrate that catalog database is replicated.

## Preconditions

- MongoDB containers are running
- `mongo-init` has exited successfully (the replica set is initialised automatically on first start)

## Main flow

1. Evaluator runs the replica set status command from the host.
2. MongoDB returns one primary and two secondary nodes.

Command:

```powershell
docker exec -it mongo1 mongosh --quiet --eval "rs.status().members.map(m => m.name + ' ' + m.stateStr)"
```

## Result

MongoDB Replica Set is verified.

---

# UC-18: Verify Kafka Event Flow

## Primary actor

Evaluator

## Goal

Demonstrate asynchronous processing.

## Preconditions

- Kafka is running
- Reviews Service is running
- Feed Service is running

## Main flow

1. User creates a review.
2. Reviews Service stores review.
3. Reviews Service publishes Kafka event.
4. Feed Service consumes event.
5. Feed Service updates Neo4j.
6. Evaluator checks logs.

## Result

Kafka-based asynchronous communication is verified.

---

# UC-19: View Neo4j Graph

## Primary actor

Evaluator

## Goal

Visualize users, reviews, movies, and relationships.

## Preconditions

- Neo4j is running
- Reviews and follows exist

## Main flow

1. Evaluator opens Neo4j Browser.
2. Evaluator logs in.
3. Evaluator runs query:

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50;
```

4. Neo4j displays graph.

## Result

Graph structure confirms social feed functionality.