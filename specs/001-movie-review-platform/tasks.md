# Task Breakdown

## Phase 1: Project Setup

- [x] Create project folder structure
- [x] Create Docker Compose file
- [x] Add Dockerfiles
- [x] Add requirements files
- [x] Create frontend folder
- [x] Create docs folder
- [x] Create specs folder

## Phase 2: Infrastructure

- [x] Add PostgreSQL for Auth Service
- [x] Add PostgreSQL for Reviews Service
- [x] Add Redis
- [x] Add MongoDB nodes
- [x] Configure MongoDB Replica Set command
- [x] Add Kafka and Zookeeper
- [x] Add Neo4j
- [x] Add Docker network
- [x] Add volumes
- [x] Add healthchecks for Postgres, Redis, Mongo, Zookeeper, Kafka, Neo4j
- [x] Add `mongo-init` one-shot service for automatic `rs.initiate()`
- [x] Wire `catalog-service` to wait on `mongo-init: service_completed_successfully`

## Phase 3: Auth Service

- [x] Implement user model
- [x] Implement register endpoint
- [x] Implement password hashing
- [x] Implement login endpoint
- [x] Implement JWT generation
- [x] Store token id in Redis
- [x] Implement token verification
- [x] Implement logout
- [x] Implement `/me`
- [x] Implement `/users`
- [x] Implement `/users/by-username/{username}`
- [x] Add two Auth Service instances
- [x] Test failover with Redis

## Phase 4: Catalog Service

- [x] Implement movie model
- [x] Connect to MongoDB Replica Set
- [x] Implement create movie
- [x] Implement get all movies
- [x] Implement get movie by id
- [x] Implement search by title
- [x] Implement search by genre
- [x] Implement search by year
- [x] Test MongoDB Replica Set status
- [x] Test Catalog API

## Phase 5: Reviews Service

- [x] Implement review model
- [x] Connect to PostgreSQL
- [x] Implement create review
- [x] Implement get all reviews
- [x] Implement get reviews by movie
- [x] Implement get reviews by user
- [x] Add Kafka producer
- [x] Publish `review.created` event
- [x] Test Kafka topic creation
- [x] Test review event logs

## Phase 6: Feed Service

- [x] Connect to Neo4j
- [x] Create Neo4j constraints
- [x] Implement follow user
- [x] Implement get feed
- [x] Implement recommendations
- [x] Add Kafka consumer
- [x] Consume `review.created`
- [x] Store User, Review, Item nodes
- [x] Store FOLLOWS, WROTE, ABOUT, REVIEWED relationships
- [x] Test feed endpoint
- [x] Test Neo4j graph query

## Phase 7: API Gateway

- [x] Implement API Gateway with FastAPI
- [x] Add proxy logic
- [x] Add Auth routes
- [x] Add Catalog routes
- [x] Add Reviews routes
- [x] Add Feed routes
- [x] Add health routes
- [x] Test all services through Gateway

## Phase 8: Frontend

- [x] Implement Streamlit UI
- [x] Add login gate
- [x] Add register and login
- [x] Add Catalog page
- [x] Add Reviews page
- [x] Add Feed page
- [x] Add Users page
- [x] Add System health page
- [x] Add Profile page
- [x] Add username-based follow
- [x] Add movie names in reviews
- [x] Add Open reviews for movie button
- [x] Add Seed Demo World

## Phase 9: Documentation

- [x] Write README.md
- [x] Write API specification
- [x] Write architecture document
- [x] Write backlog
- [x] Write use cases
- [x] Write SDD specification
- [x] Write demo scenarios
- [x] Write implementation plan
- [x] Write data model document
- [x] Write API contracts
- [x] Write event specification
- [x] Write traceability matrix

## Phase 10: Final Testing

- [x] Test Docker Compose startup
- [x] Test MongoDB Replica Set
- [x] Test Auth register/login/logout
- [x] Test Auth failover
- [x] Test Catalog
- [x] Test Reviews
- [x] Test Kafka event flow
- [x] Test Feed
- [x] Test Neo4j graph
- [x] Test UI
- [x] Test Seed Demo World

## Phase 11: CI

- [x] Add `.github/workflows/ci.yml`
- [x] CI job: validate `docker-compose.yml` syntax (`docker compose config`)
- [x] CI job: Python `compileall` across all services
- [x] CI job: matrix build of every service's Docker image

## Optional Future Tasks

- [ ] Add screenshots to README
- [ ] Add review editing
- [ ] Add review deletion
- [ ] Add real movie posters
- [ ] Add better recommendation algorithm
- [ ] Add API authentication checks inside Reviews and Feed
- [ ] Add Kubernetes manifests
- [ ] Add load balancing fallback in API Gateway for Auth Service
