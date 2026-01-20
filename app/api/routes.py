from __future__ import annotations

import time
from typing import Any, Optional

from fastapi import APIRouter, Body, File, Request, UploadFile

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.response import success_response
from app.services.processor import DataProcessor

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health(request: Request) -> Any:
    uptime = time.time() - request.app.state.start_time
    payload = {
        "status": "ok",
        "version": settings.app_version,
        "uptime_seconds": int(uptime),
    }
    return success_response(payload)


@router.post("/process")
async def process_data(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    payload: Optional[dict[str, Any]] = Body(default=None),
) -> Any:
    processor = DataProcessor.from_settings(settings)

    if file is None and payload is None:
        raise AppError(
            code=ErrorCode.INVALID_REQUEST,
            message="No input provided. Upload a file or send JSON.",
            status_code=400,
        )

    if file is not None and payload is not None:
        raise AppError(
            code=ErrorCode.INVALID_REQUEST,
            message="Provide either a file or a JSON payload, not both.",
            status_code=400,
        )

    if file is not None:
        result = await processor.process_upload(file)
    else:
        result = await processor.process_json_payload(payload, request)

    return success_response(result)
