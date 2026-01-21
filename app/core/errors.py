from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    SUCCESS = 0
    INVALID_REQUEST = 1001
    UNSUPPORTED_TYPE = 1002
    PARSE_ERROR = 1004
    VALIDATION_ERROR = 1005
    INTERNAL_ERROR = 2001
    MISSING_REQUIRED_SUBJECT = 1101
    INCONSISTENT_YEARS = 1102
    INVALID_AMOUNT = 1103


@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str
    status_code: int = 400
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.code.name.lower(),
            "details": self.details or {},
        }
