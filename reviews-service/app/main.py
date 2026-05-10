from fastapi import FastAPI

from app.api import router
from app.repository import init_db


app = FastAPI(
    title="Reviews Service",
    description="Movie reviews microservice with PostgreSQL and Kafka producer",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(router)