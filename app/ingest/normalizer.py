from __future__ import annotations

import pandas as pd

from app.core.errors import AppError, ErrorCode
from app.ingest.subject_parser import parse_subjects

YEAR_COLUMNS = {"year", "年份"}
AMOUNT_COLUMNS = {"amount", "金额"}


def normalize_statement(
    company_name: str,
    statement_type: str,
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(how="all")

    subject_result = parse_subjects(df)

    df["subject_path"] = subject_result.subject_path
    df["subject_l1"] = subject_result.subject_l1
    df["subject_l2"] = subject_result.subject_l2
    df["subject_l3"] = subject_result.subject_l3

    normalized_rows: list[dict] = []

    if YEAR_COLUMNS.intersection(df.columns) and AMOUNT_COLUMNS.intersection(df.columns):
        year_col = next(col for col in df.columns if col in YEAR_COLUMNS)
        amount_col = next(col for col in df.columns if col in AMOUNT_COLUMNS)
        for _, row in df.iterrows():
            normalized_rows.append(
                {
                    "company_name": company_name,
                    "statement_type": statement_type,
                    "category": row.get("subject_l1", ""),
                    "subject_path": row.get("subject_path", ""),
                    "subject_l1": row.get("subject_l1", ""),
                    "subject_l2": row.get("subject_l2", ""),
                    "subject_l3": row.get("subject_l3", ""),
                    "year": int(row[year_col]),
                    "amount": float(row[amount_col]),
                }
            )
        return pd.DataFrame(normalized_rows)

    subject_columns = {
        "subject_path",
        "subject_l1",
        "subject_l2",
        "subject_l3",
    }

    value_columns = [col for col in df.columns if col not in subject_columns]
    year_columns = [col for col in value_columns if str(col).isdigit()]
    if not year_columns:
        raise AppError(
            code=ErrorCode.PARSE_ERROR,
            message="No year columns detected in statement sheet.",
            status_code=400,
            details={"columns": value_columns},
        )

    for _, row in df.iterrows():
        for year in year_columns:
            amount = row.get(year)
            if pd.isna(amount):
                continue
            try:
                amount_value = float(amount)
            except (TypeError, ValueError) as exc:
                raise AppError(
                    code=ErrorCode.INVALID_AMOUNT,
                    message="Invalid amount value.",
                    status_code=400,
                    details={"year": year, "amount": amount},
                ) from exc
            normalized_rows.append(
                {
                    "company_name": company_name,
                    "statement_type": statement_type,
                    "category": row.get("subject_l1", ""),
                    "subject_path": row.get("subject_path", ""),
                    "subject_l1": row.get("subject_l1", ""),
                    "subject_l2": row.get("subject_l2", ""),
                    "subject_l3": row.get("subject_l3", ""),
                    "year": int(year),
                    "amount": amount_value,
                }
            )

    return pd.DataFrame(normalized_rows)
