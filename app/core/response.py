from __future__ import annotations

from typing import Any

from app.core.errors import AppError, ErrorCode


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
