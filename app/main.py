from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import configure_logging, get_logger, trace_id_middleware
from app.core.response import error_response

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.middleware("http")(trace_id_middleware)
app.include_router(router)


@app.on_event("startup")
async def startup_event() -> None:
    app.state.start_time = time.time()
    logger.info("Service started", extra={"env": settings.app_env})


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    error = AppError(
        code=ErrorCode.INVALID_REQUEST,
        message="Invalid request payload.",
        status_code=422,
        details={"errors": exc.errors()},
    )
    return error_response(error)


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", extra={"error": str(exc)})
    error = AppError(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error.",
        status_code=500,
    )
    return error_response(error)


@app.get("/")
async def root() -> Any:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
    }
