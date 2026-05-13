import os

from fastapi import FastAPI

from common.fastapi_handlers import register_exception_handlers
from common.service_discovery import start_registration_heartbeat
from app.api import router
from app.repository import init_db
from app.service import INSTANCE_NAME


app = FastAPI(
    title="Auth Service",
    description="Authentication microservice for Movie Review Platform",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    init_db()
    start_registration_heartbeat(
        service_name="auth-service",
        instance_name=INSTANCE_NAME,
        instance_url=os.getenv("PUBLIC_URL", "http://auth-service:8000"),
    )


register_exception_handlers(app)
app.include_router(router)
