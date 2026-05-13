import os

from fastapi import FastAPI

from common.fastapi_handlers import register_exception_handlers
from common.service_discovery import start_registration_heartbeat
from app.api import router
from app.repository import wait_for_mongo


INSTANCE_NAME = os.getenv("INSTANCE_NAME", "catalog-service")

app = FastAPI(
    title="Catalog Service",
    description="Movie catalog microservice with MongoDB Replica Set",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    wait_for_mongo()
    start_registration_heartbeat(
        service_name="catalog-service",
        instance_name=INSTANCE_NAME,
        instance_url=os.getenv("PUBLIC_URL", "http://catalog-service:8000"),
    )


register_exception_handlers(app)
app.include_router(router)
