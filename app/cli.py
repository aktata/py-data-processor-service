from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.logging import configure_logging, generate_trace_id, get_logger, set_trace_id
from app.services.processor import DataProcessor

logger = get_logger(__name__)


def _load_json_argument(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise AppError(
            code=ErrorCode.PARSE_ERROR,
            message="Failed to parse JSON input.",
            status_code=400,
            details={"error": str(exc)},
        ) from exc


def _build_payload(data: dict[str, Any], trace_id: str) -> dict[str, Any]:
    return {
        "code": int(ErrorCode.SUCCESS),
        "message": "success",
        "data": data,
        "trace_id": trace_id,
    }


def _build_error_payload(error: AppError, trace_id: str) -> dict[str, Any]:
    return {
        "code": int(error.code),
        "message": error.message,
        "data": error.to_dict(),
        "trace_id": trace_id,
    }


def _process_command(args: argparse.Namespace) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    processor = DataProcessor.from_settings(settings)
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    if args.file and args.json_input:
        error = AppError(
            code=ErrorCode.INVALID_REQUEST,
            message="Provide either --file or --json, not both.",
            status_code=400,
        )
        print(json.dumps(_build_error_payload(error, trace_id), ensure_ascii=False))
        return 1

    if not args.file and not args.json_input:
        error = AppError(
            code=ErrorCode.INVALID_REQUEST,
            message="Provide --file or --json input.",
            status_code=400,
        )
        print(json.dumps(_build_error_payload(error, trace_id), ensure_ascii=False))
        return 1

    try:
        if args.file:
            path = Path(args.file)
            try:
                read_start = time.perf_counter()
                raw = path.read_bytes()
            except OSError as exc:
                raise AppError(
                    code=ErrorCode.INVALID_REQUEST,
                    message="Failed to read file.",
                    status_code=400,
                    details={"path": str(path), "error": str(exc)},
                ) from exc
            parse_ms = int((time.perf_counter() - read_start) * 1000)
            result = processor.process_file_bytes(
                filename=path.name,
                content_type=None,
                raw=raw,
                parse_ms=parse_ms,
            )
        else:
            payload = _load_json_argument(args.json_input)
            result = processor.process_json_object(payload=payload, size_bytes=0, validate_ms=0)

        payload_out = _build_payload(result, trace_id)
        print(json.dumps(payload_out, ensure_ascii=False))
        return 0
    except AppError as exc:
        logger.warning("CLI processing failed", extra={"error": exc.message})
        print(json.dumps(_build_error_payload(exc, trace_id), ensure_ascii=False))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Data processor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Process JSON or file inputs.")
    process_parser.add_argument("--file", help="Path to file (CSV/JSON/image).")
    process_parser.add_argument(
        "--json",
        dest="json_input",
        help="JSON string payload (e.g. '{\"a\":1}').",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "process":
        return _process_command(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
