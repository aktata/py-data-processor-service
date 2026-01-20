from __future__ import annotations

import io
from typing import Any

from PIL import Image

from app.core.errors import AppError, ErrorCode


def analyze_image(raw: bytes) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        with Image.open(io.BytesIO(raw)) as img:
            summary = {
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "size_bytes": len(raw),
            }
    except Exception as exc:
        raise AppError(
            code=ErrorCode.PARSE_ERROR,
            message="Failed to parse image.",
            status_code=400,
            details={"error": str(exc)},
        ) from exc

    return summary, warnings
