from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.errors import AppError, ErrorCode

REQUIRED_SHEETS = {
    "balance_sheet": ["资产负债表", "balance_sheet"],
    "income_statement": ["利润表", "income_statement"],
    "cash_flow": ["现金流量表", "cash_flow"],
}


def read_company_excel(file_path: Path) -> dict[str, pd.DataFrame]:
    if not file_path.exists():
        raise AppError(
            code=ErrorCode.INVALID_REQUEST,
            message=f"Excel file not found: {file_path}",
            status_code=404,
        )

    try:
        excel = pd.ExcelFile(file_path)
    except Exception as exc:
        raise AppError(
            code=ErrorCode.PARSE_ERROR,
            message="Failed to read Excel file.",
            status_code=400,
            details={"error": str(exc)},
        ) from exc

    sheet_map: dict[str, pd.DataFrame] = {}

    for statement_type, aliases in REQUIRED_SHEETS.items():
        sheet_name = next((name for name in aliases if name in excel.sheet_names), None)
        if not sheet_name:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"Missing required sheet for {statement_type}.",
                status_code=400,
            )
        sheet_map[statement_type] = excel.parse(sheet_name)

    return sheet_map
