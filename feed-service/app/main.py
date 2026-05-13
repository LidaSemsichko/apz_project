import os

from fastapi import FastAPI

from common.fastapi_handlers import register_exception_handlers
from common.service_discovery import start_registration_heartbeat
from app.api import router
from app.repository import create_constraints, wait_for_neo4j


INSTANCE_NAME = os.getenv("INSTANCE_NAME", "feed-api")

app = FastAPI(
    title="Feed API",
    description="Social feed API with Neo4j",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    wait_for_neo4j()
    create_constraints()
    start_registration_heartbeat(
        service_name="feed-api",
        instance_name=INSTANCE_NAME,
        instance_url=os.getenv("PUBLIC_URL", "http://feed-api:8000"),
    )


register_exception_handlers(app)
app.include_router(router)
