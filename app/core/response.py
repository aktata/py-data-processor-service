from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.core.errors import AppError, ErrorCode
from app.core.logging import get_trace_id


def build_response_data(data: dict[str, Any], trace_id: str) -> dict[str, Any]:
    return {
        "code": int(ErrorCode.SUCCESS),
        "message": "success",
        "data": data,
        "trace_id": trace_id,
    }


def build_error_data(error: AppError, trace_id: str) -> dict[str, Any]:
    return {
        "code": int(error.code),
        "message": error.message,
        "data": error.to_dict(),
        "trace_id": trace_id,
    }


def success_response(data: dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=200, content=build_response_data(data, get_trace_id()))


def error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=build_error_data(error, get_trace_id()),
    )
