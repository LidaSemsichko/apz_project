from fastapi import FastAPI

from app.api import router
from app.repository import init_db


app = FastAPI(
    title="Auth Service",
    description="Authentication microservice for Movie Review Platform",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(router)