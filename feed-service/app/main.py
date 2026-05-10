from fastapi import FastAPI

from app.api import router
from app.repository import wait_for_neo4j, create_constraints
from app.kafka_consumer import start_consumer_thread


app = FastAPI(
    title="Feed Service",
    description="Social feed microservice with Neo4j and Kafka consumer",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    wait_for_neo4j()
    create_constraints()
    start_consumer_thread()


app.include_router(router)