from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.core.errors import AppError, ErrorCode
from app.core.logging import get_trace_id


def success_response(data: dict[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "code": int(ErrorCode.SUCCESS),
            "message": "success",
            "data": data,
            "trace_id": get_trace_id(),
        },
    )


def error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": int(error.code),
            "message": error.message,
            "data": error.to_dict(),
            "trace_id": get_trace_id(),
        },
    )
