from __future__ import annotations

import csv
import io
from collections import Counter
from typing import Any, Iterable

import chardet

from app.core.errors import AppError, ErrorCode

SUPPORTED_ENCODINGS = ["utf-8", "utf-8-sig", "gbk"]
DELIMITERS = [",", "\t", ";"]


def analyze_csv(raw: bytes) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    warnings: list[str] = []
    encoding = detect_encoding(raw)
    if encoding not in SUPPORTED_ENCODINGS:
        warnings.append(f"Detected encoding {encoding}. Attempting to decode anyway.")

    try:
        decoded = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        raise AppError(
            code=ErrorCode.PARSE_ERROR,
            message="Failed to decode CSV file.",
            status_code=400,
            details={"encoding": encoding, "error": str(exc)},
        ) from exc

    delimiter = detect_delimiter(decoded)
    if delimiter != ",":
        warnings.append(f"Detected delimiter '{delimiter}'.")

    reader = csv.reader(io.StringIO(decoded), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="CSV file is empty.",
            status_code=400,
        )

    columns = [col.strip() for col in rows[0]]
    data_rows = rows[1:]

    missing = _missing_values(columns, data_rows)
    dtypes = _infer_dtypes(columns, data_rows)

    summary = {
        "rows": len(data_rows),
        "cols": len(columns),
        "columns": columns,
        "missing_values_per_column": missing,
        "dtypes": dtypes,
    }
    metadata = {"encoding": encoding, "delimiter": delimiter}
    return summary, warnings, metadata


def detect_encoding(raw: bytes) -> str:
    detection = chardet.detect(raw)
    encoding = (detection.get("encoding") or "utf-8").lower()
    if encoding in SUPPORTED_ENCODINGS:
        return encoding
    return encoding


def detect_delimiter(decoded: str) -> str:
    sample = "\n".join(decoded.splitlines()[:5])
    scores: dict[str, int] = {}
    for delimiter in DELIMITERS:
        try:
            reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
            counts = [len(row) for row in reader if row]
        except csv.Error:
            counts = []
        scores[delimiter] = _consistency_score(counts)
    return max(scores, key=scores.get)


def _consistency_score(counts: Iterable[int]) -> int:
    if not counts:
        return 0
    counter = Counter(counts)
    most_common = counter.most_common(1)[0][1]
    return most_common


def _missing_values(columns: list[str], rows: list[list[str]]) -> dict[str, int]:
    missing: dict[str, int] = {col: 0 for col in columns}
    for row in rows:
        for idx, col in enumerate(columns):
            value = row[idx].strip() if idx < len(row) else ""
            if value == "" or value.lower() == "null":
                missing[col] += 1
    return missing


def _infer_dtypes(columns: list[str], rows: list[list[str]]) -> dict[str, str]:
    dtypes: dict[str, str] = {}
    for idx, col in enumerate(columns):
        values = [row[idx].strip() for row in rows if idx < len(row)]
        dtypes[col] = _infer_series_type(values)
    return dtypes


def _infer_series_type(values: list[str]) -> str:
    if not values:
        return "unknown"

    def is_int(value: str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False

    def is_float(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    def is_bool(value: str) -> bool:
        return value.lower() in {"true", "false"}

    types = []
    for value in values:
        if value == "":
            continue
        if is_bool(value):
            types.append("bool")
        elif is_int(value):
            types.append("int")
        elif is_float(value):
            types.append("float")
        else:
            types.append("str")

    if not types:
        return "unknown"

    if all(t == "int" for t in types):
        return "int"
    if all(t in {"int", "float"} for t in types):
        return "float"
    if all(t == "bool" for t in types):
        return "bool"
    return "str"
