from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import pandas as pd

from app.core.errors import AppError, ErrorCode


@dataclass
class SubjectParseResult:
    subject_path: list[str]
    subject_l1: list[str]
    subject_l2: list[str]
    subject_l3: list[str]


def _normalize_text(value: str) -> str:
    return str(value).strip()


def _split_by_delimiter(value: str) -> list[str]:
    for delimiter in [">", "/", "-", "\\"]:
        if delimiter in value:
            return [_normalize_text(part) for part in value.split(delimiter) if _normalize_text(part)]
    return [_normalize_text(value)]


def _parse_by_indent(values: Sequence[str]) -> list[list[str]]:
    levels: list[list[str]] = []
    indent_values = [len(str(val)) - len(str(val).lstrip(" ")) for val in values]
    unique_indents = sorted(set(indent_values))
    if len(unique_indents) <= 1:
        raise AppError(
            code=ErrorCode.PARSE_ERROR,
            message="Unable to infer subject hierarchy from indentation.",
            status_code=400,
        )
    indent_to_level = {indent: idx + 1 for idx, indent in enumerate(unique_indents)}
    current_levels = {1: "", 2: "", 3: ""}

    for raw_value, indent in zip(values, indent_values, strict=False):
        level = indent_to_level.get(indent, 1)
        cleaned = _normalize_text(raw_value)
        current_levels[level] = cleaned
        for higher in range(level + 1, 4):
            current_levels[higher] = ""
        levels.append([current_levels.get(1, ""), current_levels.get(2, ""), current_levels.get(3, "")])

    return levels


def parse_subjects(df: pd.DataFrame) -> SubjectParseResult:
    columns = [str(col).strip() for col in df.columns]
    df = df.copy()
    df.columns = columns

    candidate_multi = {
        "subject_l1": ["subject_l1", "一级科目", "一级"],
        "subject_l2": ["subject_l2", "二级科目", "二级"],
        "subject_l3": ["subject_l3", "三级科目", "三级"],
    }

    def find_column(options: Iterable[str]) -> str | None:
        for option in options:
            if option in df.columns:
                return option
        return None

    l1_col = find_column(candidate_multi["subject_l1"])
    l2_col = find_column(candidate_multi["subject_l2"])
    l3_col = find_column(candidate_multi["subject_l3"])

    if l1_col:
        l1 = df[l1_col].fillna("").astype(str).map(_normalize_text).tolist()
        l2 = (
            df[l2_col].fillna("").astype(str).map(_normalize_text).tolist()
            if l2_col
            else [""] * len(df)
        )
        l3 = (
            df[l3_col].fillna("").astype(str).map(_normalize_text).tolist()
            if l3_col
            else [""] * len(df)
        )
        subject_path = [
            ">".join([val for val in row if val]) for row in zip(l1, l2, l3, strict=False)
        ]
        return SubjectParseResult(subject_path=subject_path, subject_l1=l1, subject_l2=l2, subject_l3=l3)

    subject_col = find_column(["subject_path", "subject", "科目", "项目"])
    if not subject_col:
        subject_col = df.columns[0]

    values = df[subject_col].fillna("").astype(str).tolist()

    if any(
        delimiter in str(value) for value in values for delimiter in [">", "/", "-", "\\"]
    ):
        parsed = [_split_by_delimiter(value) for value in values]
    else:
        try:
            parsed = _parse_by_indent(values)
        except AppError:
            parsed = [_split_by_delimiter(value) for value in values]

    l1: list[str] = []
    l2: list[str] = []
    l3: list[str] = []
    subject_path: list[str] = []

    for parts in parsed:
        parts = [part for part in parts if part]
        padded = (parts + ["", "", ""])[:3]
        l1.append(padded[0])
        l2.append(padded[1])
        l3.append(padded[2])
        subject_path.append(">".join([part for part in padded if part]))

    return SubjectParseResult(subject_path=subject_path, subject_l1=l1, subject_l2=l2, subject_l3=l3)
