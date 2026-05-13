from fastapi import FastAPI
from fastapi.responses import JSONResponse

from common.errors import AppError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_, error: AppError):
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
        )
