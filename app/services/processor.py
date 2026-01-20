from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Tuple

from fastapi import Request, UploadFile

from app.config import AppSettings, UploadConstraints
from app.core.errors import AppError, ErrorCode
from app.core.logging import get_logger
from app.utils import csv_tools, filetype, image_tools, json_tools

logger = get_logger(__name__)


@dataclass
class InputObject:
    source: str
    input_type: str
    filename: str | None
    content_type: str | None
    size_bytes: int
    parsed_object: Any | None


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

    async def process_request(
        self,
        *,
        file: UploadFile | None,
        payload: Any | None,
        request: Request,
    ) -> dict[str, Any]:
        if file is not None:
            parse_start = time.perf_counter()
            raw = await file.read()
            parse_ms = self._elapsed_ms(parse_start)
            return self.process_file_bytes(
                filename=file.filename,
                content_type=file.content_type,
                raw=raw,
                parse_ms=parse_ms,
            )
        validate_start = time.perf_counter()
        size_bytes = self._validate_json_payload(payload, request)
        validate_ms = self._elapsed_ms(validate_start)
        return self.process_json_object(
            payload=payload,
            size_bytes=size_bytes,
            validate_ms=validate_ms,
        )

    def process_file_bytes(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        raw: bytes,
        parse_ms: int | None = None,
    ) -> dict[str, Any]:
        start_total = time.perf_counter()
        timings = {"parse": 0, "validate": 0, "process": 0, "total": 0}

        size_bytes = len(raw)
        timings["parse"] = parse_ms if parse_ms is not None else 0

        validate_start = time.perf_counter()
        self._check_payload_size(size_bytes)
        input_type = filetype.detect_input_type(filename, content_type)
        timings["validate"] = self._elapsed_ms(validate_start)

        logger.info(
            "Processing upload",
            extra={
                "input_type": input_type,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
            },
        )

        process_start = time.perf_counter()
        summary, warnings, parsed_object = self._process_bytes_by_type(input_type, raw)
        timings["process"] = self._elapsed_ms(process_start)

        input_obj = InputObject(
            source="file_upload",
            input_type=input_type,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            parsed_object=parsed_object,
        )

        timings["total"] = self._elapsed_ms(start_total)
        return self._build_response(input_obj, summary, warnings, timings)

    def process_json_object(
        self,
        *,
        payload: Any | None,
        size_bytes: int = 0,
        validate_ms: int = 0,
    ) -> dict[str, Any]:
        if payload is None:
            raise AppError(
                code=ErrorCode.INVALID_REQUEST,
                message="JSON payload is required.",
                status_code=400,
            )
        start_total = time.perf_counter()
        timings = {"parse": 0, "validate": 0, "process": 0, "total": 0}
        timings["validate"] = validate_ms

        parse_start = time.perf_counter()
        parsed = payload
        timings["parse"] = self._elapsed_ms(parse_start)

        process_start = time.perf_counter()
        summary, warnings = json_tools.analyze_json(
            parsed,
            max_depth=self.constraints.json_max_depth,
            max_nodes=self.constraints.json_max_nodes,
        )
        timings["process"] = self._elapsed_ms(process_start)

        input_obj = InputObject(
            source="json_body",
            input_type="json",
            filename=None,
            content_type="application/json",
            size_bytes=size_bytes,
            parsed_object=parsed,
        )

        timings["total"] = self._elapsed_ms(start_total)
        return self._build_response(input_obj, summary, warnings, timings)

    def _process_bytes_by_type(
        self, input_type: str, raw: bytes
    ) -> Tuple[dict[str, Any], list[str], Any | None]:
        if input_type == "csv":
            summary, warnings, metadata = csv_tools.analyze_csv(raw)
            return summary, warnings, metadata
        if input_type == "json":
            payload = self._parse_json_bytes(raw)
            summary, warnings = json_tools.analyze_json(
                payload,
                max_depth=self.constraints.json_max_depth,
                max_nodes=self.constraints.json_max_nodes,
            )
            return summary, warnings, payload
        if input_type == "image":
            summary, warnings = image_tools.analyze_image(raw)
            return summary, warnings, summary

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

    def _build_response(
        self,
        input_obj: InputObject,
        summary: dict[str, Any],
        warnings: list[str],
        timings: dict[str, int],
    ) -> dict[str, Any]:
        payload = {
            "input_type": input_obj.input_type,
            "source": input_obj.source,
            "summary": summary,
            "warnings": warnings,
            "timings_ms": timings,
            "limits": {
                "max_bytes": self.constraints.max_bytes,
                "json_max_depth": self.constraints.json_max_depth,
                "json_max_nodes": self.constraints.json_max_nodes,
            },
        }
        return payload

    def _validate_json_payload(self, payload: Any | None, request: Request) -> int:
        if payload is None:
            raise AppError(
                code=ErrorCode.INVALID_REQUEST,
                message="JSON payload is required.",
                status_code=400,
            )

        content_length = request.headers.get("content-length")
        size_bytes = int(content_length) if content_length else 0
        if content_length and size_bytes > self.constraints.max_bytes:
            raise AppError(
                code=ErrorCode.PAYLOAD_TOO_LARGE,
                message="JSON payload exceeds size limit.",
                status_code=413,
            )
        return size_bytes

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return int((time.perf_counter() - start) * 1000)
