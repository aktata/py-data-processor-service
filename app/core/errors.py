from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional


class ErrorCode(IntEnum):
    SUCCESS = 0
    INVALID_REQUEST = 1001
    UNSUPPORTED_TYPE = 1002
    PAYLOAD_TOO_LARGE = 1003
    PARSE_ERROR = 1004
    VALIDATION_ERROR = 1005
    INTERNAL_ERROR = 2001


@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str
    status_code: int = 400
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.code.name.lower(),
            "details": self.details or {},
        }
