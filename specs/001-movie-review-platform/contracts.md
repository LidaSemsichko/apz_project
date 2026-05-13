# API Contracts

## 1. Overview

This document describes API contracts used by the Movie Review Platform.

External clients communicate with the system through API Gateway:

```text
http://localhost:8000
```

## 2. Auth Contracts

### Register

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

### Login

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

### Verify

```http
GET /auth/verify
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

### Current User

```http
GET /auth/me
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

### Logout

```http
POST /auth/logout
Authorization: Bearer <jwt-token>
```

Response:

```json
{
  "message": "Logged out successfully",
  "instance": "auth-service-1"
}
```

### Users

```http
GET /auth/users
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

### User by Username

```http
GET /auth/users/by-username/{username}
```

Response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username"
}
```

## 3. Catalog Contracts

### Create Movie

```http
POST /catalog
```

Request:

```json
{
  "title": "Interstellar",
  "description": "A science fiction film about space and time.",
  "genres": ["Sci-Fi", "Drama"],
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
  "description": "A science fiction film about space and time.",
  "genres": ["Sci-Fi", "Drama"],
  "year": 2014,
  "director": "Christopher Nolan",
  "poster_url": "https://example.com/interstellar.jpg"
}
```

### Get All Movies

```http
GET /catalog
```

Response:

```json
[
  {
    "id": "movie-id",
    "title": "Interstellar",
    "description": "A science fiction film about space and time.",
    "genres": ["Sci-Fi", "Drama"],
    "year": 2014,
    "director": "Christopher Nolan",
    "poster_url": "https://example.com/interstellar.jpg"
  }
]
```

### Search Movies

```http
GET /catalog/search?title=inter
GET /catalog/search?genre=Sci-Fi
GET /catalog/search?year=2014
```

Response:

```json
[
  {
    "id": "movie-id",
    "title": "Interstellar",
    "description": "A science fiction film about space and time.",
    "genres": ["Sci-Fi", "Drama"],
    "year": 2014,
    "director": "Christopher Nolan",
    "poster_url": "https://example.com/interstellar.jpg"
  }
]
```

## 4. Reviews Contracts

### Create Review

```http
POST /reviews
```

Request:

```json
{
  "item_id": "movie-id",
  "text": "Amazing movie.",
  "rating": 10
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "item_id": "movie-id",
  "text": "Amazing movie.",
  "rating": 10,
  "created_at": "2026-05-10T13:05:03.411227"
}
```

### Get All Reviews

```http
GET /reviews
```

### Get Reviews by Movie

```http
GET /reviews/item/{item_id}
```

### Get Reviews by User

```http
GET /reviews/user/{user_id}
```

## 5. Feed Contracts

### Follow User

```http
POST /feed/follow/{following_id}
```

Response:

```json
{
  "message": "User followed successfully",
  "follower_id": 1,
  "following_id": 2
}
```

### Get Feed

```http
GET /feed
```

Response:

```json
[
  {
    "review_id": 2,
    "user_id": 2,
    "item_id": "movie-id",
    "text": "A visually powerful movie.",
    "rating": 9,
    "created_at": "2026-05-10T13:10:06.167602"
  }
]
```

### Get Recommendations

```http
GET /feed/recommendations
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

## 6. Health Contracts

```http
GET /health
GET /auth/health
GET /catalog/health
GET /reviews/health
GET /feed/health
```

Expected response format:

```json
{
  "status": "ok",
  "service": "service-name"
}
```
