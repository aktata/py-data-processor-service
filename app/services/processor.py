from __future__ import annotations

import json
import time
from typing import Any, Tuple

from fastapi import Request, UploadFile

from app.config import AppSettings, UploadConstraints
from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger
from app.utils import csv_tools, filetype, image_tools, json_tools

logger = get_logger(__name__)


class DataProcessor:
    def __init__(self, constraints: UploadConstraints) -> None:
        self.constraints = constraints

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "DataProcessor":
        return cls(
            UploadConstraints(
                max_bytes=settings.max_upload_size_mb * 1024 * 1024,
                json_max_depth=settings.json_max_depth,
                json_max_nodes=settings.json_max_nodes,
            )
        )

    async def process_upload(self, file: UploadFile) -> dict[str, Any]:
        start_total = time.perf_counter()
        parse_start = time.perf_counter()
        raw = await file.read()
        parse_ms = self._elapsed_ms(parse_start)

        self._check_payload_size(len(raw))

        input_type = filetype.detect_input_type(file.filename, file.content_type)
        logger.info(
            "Processing upload",
            extra={
                "input_type": input_type,
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(raw),
            },
        )

        validate_start = time.perf_counter()
        summary, warnings = self._process_bytes_by_type(input_type, raw)
        validate_ms = self._elapsed_ms(validate_start)

        total_ms = self._elapsed_ms(start_total)
        return self._build_response(input_type, summary, warnings, parse_ms, validate_ms, total_ms)

    async def process_json_payload(
        self, payload: Any | None, request: Request
    ) -> dict[str, Any]:
        if payload is None:
            raise AppError(
                code=ErrorCode.INVALID_REQUEST,
                message="JSON payload is required.",
                status_code=400,
            )

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.constraints.max_bytes:
            raise AppError(
                code=ErrorCode.PAYLOAD_TOO_LARGE,
                message="JSON payload exceeds size limit.",
                status_code=413,
            )

        start_total = time.perf_counter()
        parse_start = time.perf_counter()
        parsed = payload
        parse_ms = self._elapsed_ms(parse_start)

        validate_start = time.perf_counter()
        summary, warnings = json_tools.analyze_json(
            parsed,
            max_depth=self.constraints.json_max_depth,
            max_nodes=self.constraints.json_max_nodes,
        )
        validate_ms = self._elapsed_ms(validate_start)

        total_ms = self._elapsed_ms(start_total)
        return self._build_response("json", summary, warnings, parse_ms, validate_ms, total_ms)

    def _process_bytes_by_type(self, input_type: str, raw: bytes) -> Tuple[dict[str, Any], list[str]]:
        if input_type == "csv":
            summary, warnings = csv_tools.analyze_csv(raw)
            return summary, warnings
        if input_type == "json":
            payload = self._parse_json_bytes(raw)
            summary, warnings = json_tools.analyze_json(
                payload,
                max_depth=self.constraints.json_max_depth,
                max_nodes=self.constraints.json_max_nodes,
            )
            return summary, warnings
        if input_type == "image":
            summary, warnings = image_tools.analyze_image(raw)
            return summary, warnings

        raise AppError(
            code=ErrorCode.UNSUPPORTED_TYPE,
            message="Unsupported file type.",
            status_code=415,
            details={"filename": "unknown"},
        )

    def _parse_json_bytes(self, raw: bytes) -> Any:
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise AppError(
                code=ErrorCode.PARSE_ERROR,
                message="Failed to parse JSON payload.",
                status_code=400,
                details={"error": str(exc)},
            ) from exc
        except UnicodeDecodeError as exc:
            raise AppError(
                code=ErrorCode.PARSE_ERROR,
                message="JSON payload must be UTF-8 encoded.",
                status_code=400,
                details={"error": str(exc)},
            ) from exc

    def _check_payload_size(self, size_bytes: int) -> None:
        if size_bytes > self.constraints.max_bytes:
            raise AppError(
                code=ErrorCode.PAYLOAD_TOO_LARGE,
                message="Payload exceeds size limit.",
                status_code=413,
                details={"max_bytes": self.constraints.max_bytes},
            )

    @staticmethod
    def _build_response(
        input_type: str,
        summary: dict[str, Any],
        warnings: list[str],
        parse_ms: int,
        validate_ms: int,
        total_ms: int,
    ) -> dict[str, Any]:
        payload = {
            "input_type": input_type,
            "summary": summary,
            "timings_ms": {
                "parse": parse_ms,
                "validate": validate_ms,
                "process": validate_ms,
                "total": total_ms,
            },
            "warnings": warnings,
        }
        return payload

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return int((time.perf_counter() - start) * 1000)
