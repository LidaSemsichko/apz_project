import os
import random

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response


CONFIG_SERVER_URL = os.getenv("CONFIG_SERVER_URL", "http://config-server:8000")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "api-gateway")

SERVICE_NAMES = {
    "auth": "auth-service",
    "catalog": "catalog-service",
    "reviews": "reviews-service",
    "feed": "feed-api",
}

HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


app = FastAPI(
    title="API Gateway",
    description="Single entry point for Movie Review Platform",
    version="1.0.0",
)


def forwarded_headers(request: Request) -> dict:
    return {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


async def resolve_instances(client: httpx.AsyncClient, service_name: str) -> list[dict]:
    try:
        response = await client.get(f"{CONFIG_SERVER_URL}/services/{service_name}")
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(
                status_code=502,
                detail=f"No active instances registered for {service_name}",
            )
        raise HTTPException(status_code=502, detail=f"Cannot resolve {service_name}") from error
    except httpx.RequestError as error:
        raise HTTPException(status_code=502, detail=f"Config server unavailable: {error}") from error

    return response.json().get("instances", [])


async def call_service(
    client: httpx.AsyncClient,
    service_name: str,
    method: str,
    path: str,
    *,
    headers: dict | None = None,
    content: bytes | None = None,
    query_string: str = "",
) -> httpx.Response:
    instances = await resolve_instances(client, service_name)
    random.shuffle(instances)
    last_error: Exception | None = None
    last_response: httpx.Response | None = None

    for instance in instances:
        target_url = f"{instance['instance_url'].rstrip('/')}/{path.lstrip('/')}"
        if query_string:
            target_url = f"{target_url}?{query_string}"

        try:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=content,
            )
            if response.status_code >= 500 and len(instances) > 1:
                last_response = response
                continue
            return response
        except httpx.RequestError as error:
            last_error = error

    if last_response is not None:
        return last_response

    raise HTTPException(
        status_code=502,
        detail=f"{service_name} unavailable: {last_error}",
    )


async def verify_authorization(request: Request, client: httpx.AsyncClient) -> dict:
    authorization = request.headers.get("authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    response = await call_service(
        client,
        "auth-service",
        "GET",
        "verify",
        headers={"Authorization": authorization},
    )
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail=response.json().get("detail", "Invalid token"))
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def proxy_request(
    request: Request,
    service_name: str,
    path: str,
    *,
    require_auth: bool,
) -> Response:
    method = request.method
    body = await request.body()
    headers = forwarded_headers(request)
    query_string = request.url.query

    async with httpx.AsyncClient(timeout=20.0) as client:
        if require_auth:
            await verify_authorization(request, client)

        response = await call_service(
            client,
            service_name,
            method,
            path,
            headers=headers,
            content=body,
            query_string=query_string,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


async def get_json(
    client: httpx.AsyncClient,
    request: Request,
    service_name: str,
    path: str,
    *,
    query_string: str = "",
):
    response = await call_service(
        client,
        service_name,
        "GET",
        path,
        headers=forwarded_headers(request),
        query_string=query_string,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def enrich_review_items(items: list[dict], users: list[dict], movies: list[dict]) -> list[dict]:
    users_map = {user["id"]: user for user in users}
    movies_map = {movie["id"]: movie for movie in movies}

    enriched = []
    for item in items:
        user = users_map.get(item.get("user_id"))
        movie = movies_map.get(item.get("item_id"))
        enriched.append(
            {
                **item,
                "username": user["username"] if user else None,
                "movie": movie,
            }
        )
    return enriched


@app.get("/health")
async def health():
    dependencies = {"config-server": "unavailable"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{CONFIG_SERVER_URL}/health")
            dependencies["config-server"] = "ok" if response.status_code == 200 else "unavailable"
        except httpx.RequestError:
            dependencies["config-server"] = "unavailable"

        for service_name in SERVICE_NAMES.values():
            try:
                instances = await resolve_instances(client, service_name)
                dependencies[service_name] = "ok" if instances else "unavailable"
            except HTTPException:
                dependencies[service_name] = "unavailable"

    status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
    return {
        "status": status,
        "service": "api-gateway",
        "instance": INSTANCE_NAME,
        "dependencies": dependencies,
    }


@app.get("/")
def root():
    return {
        "message": "Movie Review Platform API Gateway is running",
        "routes": {
            "auth": "/auth",
            "catalog": "/catalog",
            "reviews": "/reviews",
            "feed": "/feed",
        },
    }


@app.get("/auth/health")
async def auth_health(request: Request):
    return await proxy_request(request, "auth-service", "health", require_auth=False)


@app.get("/catalog/health")
async def catalog_health(request: Request):
    return await proxy_request(request, "catalog-service", "health", require_auth=False)


@app.get("/reviews/health")
async def reviews_health(request: Request):
    return await proxy_request(request, "reviews-service", "health", require_auth=False)


@app.get("/feed/health")
async def feed_health(request: Request):
    return await proxy_request(request, "feed-api", "health", require_auth=False)


@app.get("/feed/enriched")
async def feed_enriched(request: Request):
    async with httpx.AsyncClient(timeout=20.0) as client:
        await verify_authorization(request, client)
        feed = await get_json(client, request, "feed-api", "feed")
        users = await get_json(client, request, "auth-service", "users")
        movies = await get_json(client, request, "catalog-service", "catalog")
    return enrich_review_items(feed, users, movies)


@app.get("/reviews/enriched")
async def reviews_enriched(
    request: Request,
    item_id: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
):
    async with httpx.AsyncClient(timeout=20.0) as client:
        await verify_authorization(request, client)
        if item_id:
            reviews = await get_json(client, request, "reviews-service", f"reviews/item/{item_id}")
        elif user_id:
            reviews = await get_json(client, request, "reviews-service", f"reviews/user/{user_id}")
        else:
            reviews = await get_json(client, request, "reviews-service", "reviews")
        users = await get_json(client, request, "auth-service", "users")
        movies = await get_json(client, request, "catalog-service", "catalog")
    return enrich_review_items(reviews, users, movies)


@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(path: str, request: Request):
    public = request.method == "POST" and path in {"register", "login"}
    return await proxy_request(request, "auth-service", path, require_auth=not public)


@app.api_route("/catalog", methods=["GET", "POST"])
async def catalog_root_proxy(request: Request):
    return await proxy_request(request, "catalog-service", "catalog", require_auth=True)


@app.api_route("/catalog/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catalog_proxy(path: str, request: Request):
    return await proxy_request(request, "catalog-service", f"catalog/{path}", require_auth=True)


@app.api_route("/reviews", methods=["GET", "POST"])
async def reviews_root_proxy(request: Request):
    return await proxy_request(request, "reviews-service", "reviews", require_auth=True)


@app.api_route("/reviews/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def reviews_proxy(path: str, request: Request):
    return await proxy_request(request, "reviews-service", f"reviews/{path}", require_auth=True)


@app.api_route("/feed", methods=["GET", "POST"])
async def feed_root_proxy(request: Request):
    return await proxy_request(request, "feed-api", "feed", require_auth=True)


@app.api_route("/feed/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def feed_proxy(path: str, request: Request):
    return await proxy_request(request, "feed-api", path, require_auth=True)
