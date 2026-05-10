import os

import httpx
from fastapi import FastAPI, Request, Response, HTTPException


AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service-1:8000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8000")
REVIEWS_SERVICE_URL = os.getenv("REVIEWS_SERVICE_URL", "http://reviews-service:8000")
FEED_SERVICE_URL = os.getenv("FEED_SERVICE_URL", "http://feed-service:8000")


app = FastAPI(
    title="API Gateway",
    description="Single entry point for Movie Review Platform",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "api-gateway",
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


async def proxy_request(request: Request, target_base_url: str, path: str):
    method = request.method
    body = await request.body()

    headers = dict(request.headers)
    headers.pop("host", None)

    query_string = request.url.query
    target_url = f"{target_base_url}/{path}"

    if query_string:
        target_url = f"{target_url}?{query_string}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                media_type=response.headers.get("content-type"),
            )

        except httpx.RequestError as error:
            raise HTTPException(
                status_code=502,
                detail=f"Service unavailable: {str(error)}",
            )


@app.get("/auth/health")
async def auth_health(request: Request):
    return await proxy_request(request, AUTH_SERVICE_URL, "health")


@app.get("/catalog/health")
async def catalog_health(request: Request):
    return await proxy_request(request, CATALOG_SERVICE_URL, "health")


@app.get("/reviews/health")
async def reviews_health(request: Request):
    return await proxy_request(request, REVIEWS_SERVICE_URL, "health")


@app.get("/feed/health")
async def feed_health(request: Request):
    return await proxy_request(request, FEED_SERVICE_URL, "health")


# Auth routes:
# /auth/register -> auth-service /register
# /auth/login    -> auth-service /login
# /auth/me       -> auth-service /me
# /auth/users    -> auth-service /users
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(path: str, request: Request):
    return await proxy_request(request, AUTH_SERVICE_URL, path)


# Catalog routes:
# /catalog        -> catalog-service /catalog
# /catalog/search -> catalog-service /catalog/search
# /catalog/{id}   -> catalog-service /catalog/{id}
@app.api_route("/catalog", methods=["GET", "POST"])
async def catalog_root_proxy(request: Request):
    return await proxy_request(request, CATALOG_SERVICE_URL, "catalog")


@app.api_route("/catalog/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catalog_proxy(path: str, request: Request):
    return await proxy_request(request, CATALOG_SERVICE_URL, f"catalog/{path}")


# Reviews routes:
# /reviews              -> reviews-service /reviews
# /reviews/item/{id}    -> reviews-service /reviews/item/{id}
# /reviews/user/{id}    -> reviews-service /reviews/user/{id}
@app.api_route("/reviews", methods=["GET", "POST"])
async def reviews_root_proxy(request: Request):
    return await proxy_request(request, REVIEWS_SERVICE_URL, "reviews")


@app.api_route("/reviews/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def reviews_proxy(path: str, request: Request):
    return await proxy_request(request, REVIEWS_SERVICE_URL, f"reviews/{path}")


# Feed routes:
# /feed                       -> feed-service /feed
# /feed/follow/{id}           -> feed-service /follow/{id}
# /feed/recommendations       -> feed-service /recommendations
# /feed/users/{id}/reviews    -> feed-service /users/{id}/reviews
@app.api_route("/feed", methods=["GET", "POST"])
async def feed_root_proxy(request: Request):
    return await proxy_request(request, FEED_SERVICE_URL, "feed")


@app.api_route("/feed/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def feed_proxy(path: str, request: Request):
    return await proxy_request(request, FEED_SERVICE_URL, path)