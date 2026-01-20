from __future__ import annotations

import os

from app.core.errors import AppError, ErrorCode

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_CSV_EXTS = {".csv", ".tsv"}
SUPPORTED_JSON_EXTS = {".json"}


def detect_input_type(filename: str | None, content_type: str | None) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    ct = (content_type or "").lower()

    if ext in SUPPORTED_CSV_EXTS or "text/csv" in ct:
        return "csv"
    if ext in SUPPORTED_JSON_EXTS or "application/json" in ct:
        return "json"
    if ext in SUPPORTED_IMAGE_EXTS or ct.startswith("image/"):
        return "image"

    raise AppError(
        code=ErrorCode.UNSUPPORTED_TYPE,
        message="Unsupported file type.",
        status_code=415,
        details={"filename": filename, "content_type": content_type},
    )
