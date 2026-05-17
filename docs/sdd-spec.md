# Spec-Driven Development Documentation

## 1. Purpose

This document explains how Spec-Driven Development was applied to the Movie Review Platform project.

The project uses a lightweight Spec-Driven Development approach inspired by GitHub Spec Kit and specs.md Simple Flow. The goal is to show that the system was designed and implemented based on explicit specifications, not only through ad-hoc coding.

## 2. Selected SDD Approach

The selected workflow is a lightweight SDD flow:

```text
Vision
  ↓
Functional requirements
  ↓
Technical specification
  ↓
Service design
  ↓
API contracts
  ↓
Data models
  ↓
Event models
  ↓
Implementation tasks
  ↓
Validation scenarios
```

The project was already implemented during development, so these SDD documents act as a brownfield specification layer. They document the actual system design and connect implementation details to requirements.

## 3. SDD Artifacts

The repository contains the following SDD artifacts:

```text
docs/sdd-spec.md
docs/demo-scenarios.md

specs/001-movie-review-platform/spec.md
specs/001-movie-review-platform/plan.md
specs/001-movie-review-platform/data-model.md
specs/001-movie-review-platform/contracts.md
specs/001-movie-review-platform/events.md
specs/001-movie-review-platform/tasks.md
specs/001-movie-review-platform/traceability.md
```

Additional documentation:

```text
docs/api-spec.md
docs/architecture.md
docs/backlog.md
docs/use-cases.md
```

## 4. Project Vision

Movie Review Platform is a microservice-based web application where users can register, log in, browse movies, write reviews, follow other users, and view a personalized social feed.

The project demonstrates:

- Microservice architecture
- API Gateway
- Authentication microservice
- Database-per-service design
- Redis-based token/session storage
- MongoDB Replica Set
- Kafka message queue
- Asynchronous event processing
- Neo4j graph database
- Docker Compose deployment
- Browser-based UI

## 5. Requirements Covered by the Specification

| Requirement | Specification artifact |
|---|---|
| System vision | `spec.md` |
| Functional requirements | `spec.md`, `backlog.md`, `use-cases.md` |
| Technical design | `plan.md`, `architecture.md` |
| Data models | `data-model.md` |
| API contracts | `contracts.md`, `api-spec.md` |
| Event contract | `events.md` |
| Implementation tasks | `tasks.md` |
| Requirement-to-code mapping | `traceability.md` |
| Demo and validation | `demo-scenarios.md` |

## 6. Implementation Summary

The system consists of the following services. Stateless application tiers run as two instances behind the API Gateway:

| Service | Instances | Responsibility |
|---|---|---|
| Frontend | 1 | Streamlit UI |
| API Gateway | 1 | Single entry point and request routing; resolves instances via Config Server and retries on failure |
| Config Server | 1 | Service registry (register / heartbeat / discover) |
| Auth Service | 2 | Registration, login, logout, JWT verification, user lookup |
| Catalog Service | 2 | Movie catalog stored in MongoDB Replica Set |
| Reviews Service | 2 | Review storage + transactional outbox |
| Reviews Outbox Publisher | 2 | Two workers tail the outbox table and publish to Kafka via row-level locking |
| Feed API | 2 | Feed / follow / recommendations over Neo4j |
| Feed Consumer | 2 | Same Kafka consumer group; processes `review.created` and writes Neo4j |

## 7. Data Ownership

Each service owns its own data storage:

| Service | Storage |
|---|---|
| Auth Service | PostgreSQL (`auth-db`) + Redis HA (1 master + 2 replicas + 3 sentinels) |
| Catalog Service | MongoDB Replica Set (3 nodes, `rs0`) |
| Reviews Service | PostgreSQL (`reviews-db`) with `outbox_events` table |
| Feed Service | Neo4j |

## 7.1 Secrets Management

Credentials (`JWT_SECRET`, the two Postgres user/password/db triples, Neo4j credentials) are kept out of the committed repository. `docker-compose.yml` references them as `${VAR}`; the values come from a `.env` file in the project root, which is git-ignored. A committed `.env.example` documents the variable set and provides local-dev defaults. CI provisions `.env` from `.env.example` before running `docker compose config` and fails the build on any unset variable.

## 8. Event-Driven Flow

The main asynchronous flow is review creation:

```text
User creates review
  ↓
Reviews Service stores review in PostgreSQL
  ↓
Reviews Service publishes review.created event to Kafka
  ↓
Feed Service consumes event
  ↓
Feed Service updates Neo4j graph
  ↓
Feed endpoint returns reviews from followed users
```

## 9. Validation Approach

The implementation is validated through:

- UI testing
- API Gateway health checks (`/health`, `/auth/health`, `/catalog/health`, `/reviews/health`, `/feed/health`)
- Config Server discovery check (every service should list 2 instances)
- MongoDB Replica Set status (`rs.status()`)
- Per-tier failover tests (stop one instance, verify gateway-routed traffic still works)
- Redis Sentinel failover test (stop `redis-master`, verify a replica is promoted within ~15s)
- Kafka consumer-group rebalance test (`kafka-consumer-groups --describe` before/after stopping a consumer)
- Kafka publish/consume logs
- Neo4j graph visualization
- End-to-end review-to-feed flow

## 10. Conclusion

The SDD artifacts describe what the system must do, how it is designed, how it is implemented, and how it can be verified. This makes the repository specification-driven and satisfies the requirement to provide design and specification documents alongside the source code.
