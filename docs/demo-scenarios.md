# Demo Scenarios

## 1. Start the System

From the project root:

```powershell
docker compose up -d --build
```

Check running containers:

```powershell
docker ps
```

Expected main containers:

```text
frontend
api-gateway
auth-service-1
auth-service-2
catalog-service
reviews-service
feed-service
auth-db
reviews-db
redis
mongo1
mongo2
mongo3
zookeeper
kafka
neo4j
```

## 2. Initialize MongoDB Replica Set

Open Mongo shell:

```powershell
docker exec -it mongo1 mongosh
```

Initialize the replica set:

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

Check status:

```javascript
rs.status().members.map(m => ({ name: m.name, state: m.stateStr }))
```

Expected result:

```javascript
[
  { name: 'mongo1:27017', state: 'PRIMARY' },
  { name: 'mongo2:27017', state: 'SECONDARY' },
  { name: 'mongo3:27017', state: 'SECONDARY' }
]
```

Exit shell:

```javascript
exit
```

If Catalog Service was waiting for MongoDB, restart it:

```powershell
docker restart catalog-service
```

## 3. Open the UI

Open in browser:

```text
http://localhost:8501
```

Demo flow:

1. Register or log in.
2. Open Catalog.
3. Click Seed Demo World.
4. Open Users and check demo users.
5. Open Catalog and check demo movies.
6. Open Reviews and check movie reviews.
7. Write a new review.
8. Open Feed.
9. Follow another user.
10. Check personalized feed.
11. Open reviews for a movie directly from the feed.

## 4. Check Service Health

PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/auth/health
Invoke-RestMethod http://localhost:8000/catalog/health
Invoke-RestMethod http://localhost:8000/reviews/health
Invoke-RestMethod http://localhost:8000/feed/health
```

Expected result:

```text
All services return status: ok
```

## 5. Authentication Demo

Register:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/auth/register `
  -ContentType "application/json" `
  -Body '{"email":"demo@example.com","username":"demo","password":"123456"}'
```

Login:

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"demo@example.com","password":"123456"}'

$token = $login.access_token
```

Verify:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://localhost:8000/auth/verify `
  -Headers @{Authorization = "Bearer $token"}
```

Logout:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/auth/logout `
  -Headers @{Authorization = "Bearer $token"}
```

## 6. Auth Failover Demo

Login directly through the first Auth instance:

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8001/login `
  -ContentType "application/json" `
  -Body '{"email":"demo@example.com","password":"123456"}'

$token = $login.access_token
```

Stop the first instance:

```powershell
docker stop auth-service-1
```

Verify the same token through the second instance:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://localhost:8002/verify `
  -Headers @{Authorization = "Bearer $token"}
```

Expected result:

```text
valid: true
instance: auth-service-2
```

Start the first instance again:

```powershell
docker start auth-service-1
```

## 7. Catalog Demo

Create movie:

```powershell
$movie = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/catalog `
  -ContentType "application/json" `
  -Body '{
    "title": "Interstellar",
    "description": "A science fiction film about space and time.",
    "genres": ["Sci-Fi", "Drama"],
    "year": 2014,
    "director": "Christopher Nolan",
    "poster_url": "https://example.com/interstellar.jpg"
  }'

$movieId = $movie.id
```

Get all movies:

```powershell
Invoke-RestMethod http://localhost:8000/catalog
```

Search:

```powershell
Invoke-RestMethod "http://localhost:8000/catalog/search?title=inter"
```

## 8. Reviews and Kafka Demo

Create review:

```powershell
$reviewBody = @{
  user_id = 1
  item_id = $movieId
  text = "Amazing movie with strong atmosphere."
  rating = 10
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/reviews `
  -ContentType "application/json" `
  -Body $reviewBody
```

Check Reviews Service logs:

```powershell
docker logs reviews-service --tail 100
```

Expected log:

```text
[REVIEWS] Published event to Kafka
```

Check Kafka topics:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list
```

Expected topic:

```text
review.created
```

## 9. Feed and Neo4j Demo

Check Feed Service logs:

```powershell
docker logs feed-service --tail 100
```

Expected log:

```text
[FEED] Consumed review.created event
```

Follow user:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/feed/follow/2?follower_id=1"
```

Get feed:

```powershell
Invoke-RestMethod "http://localhost:8000/feed?user_id=1"
```

## 10. Neo4j Graph Demo

Open:
http://localhost:7474


Credentials:

```text
username: neo4j
password: password123
```

Run query:

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 50;
```

Expected graph elements:

```text
User
Review
Item
FOLLOWS
WROTE
ABOUT
REVIEWED
```

## 11. Stop the System

Stop containers without deleting data:

```powershell
docker compose down
```

Stop containers and delete volumes:

```powershell
docker compose down -v
```

Warning: `-v` deletes database data.
