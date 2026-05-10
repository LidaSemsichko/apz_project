from fastapi import FastAPI

from app.api import router
from app.repository import wait_for_mongo


app = FastAPI(
    title="Catalog Service",
    description="Movie catalog microservice with MongoDB Replica Set",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    wait_for_mongo()


app.include_router(router)