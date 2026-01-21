from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.core.errors import AppError, ErrorCode


@dataclass
class IndicatorResult:
    metrics: pd.DataFrame
    warnings: list[str]


SUBJECT_RULES = {
    "net_profit": ["净利润"],
    "revenue": ["营业收入"],
    "current_assets": ["流动资产"],
    "current_liabilities": ["流动负债"],
    "equity": ["所有者权益", "股东权益"],
}


def _match_subject(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    pattern = "|".join(keywords)
    return df[df["subject_path"].str.contains(pattern, na=False)]


def _get_amount(
    facts: pd.DataFrame,
    company: str,
    year: int,
    statement_type: str,
    keywords: list[str],
) -> float:
    subset = facts[
        (facts["company_name"] == company)
        & (facts["year"] == year)
        & (facts["statement_type"] == statement_type)
    ]
    matched = _match_subject(subset, keywords)
    return matched["amount"].sum()


def calculate_indicators(
    facts: pd.DataFrame,
    missing_value_strategy: str = "warn",
) -> IndicatorResult:
    metrics: list[dict] = []
    warnings: list[str] = []

    companies = facts["company_name"].unique()

    for company in companies:
        company_years = facts[facts["company_name"] == company]["year"].unique()
        for year in company_years:
            try:
                net_profit = _get_amount(
                    facts,
                    company,
                    year,
                    "income_statement",
                    SUBJECT_RULES["net_profit"],
                )
                revenue = _get_amount(
                    facts,
                    company,
                    year,
                    "income_statement",
                    SUBJECT_RULES["revenue"],
                )
                current_assets = _get_amount(
                    facts,
                    company,
                    year,
                    "balance_sheet",
                    SUBJECT_RULES["current_assets"],
                )
                current_liabilities = _get_amount(
                    facts,
                    company,
                    year,
                    "balance_sheet",
                    SUBJECT_RULES["current_liabilities"],
                )
                equity = _get_amount(
                    facts,
                    company,
                    year,
                    "balance_sheet",
                    SUBJECT_RULES["equity"],
                )
            except KeyError as exc:
                raise AppError(
                    code=ErrorCode.MISSING_REQUIRED_SUBJECT,
                    message="Missing required subject mapping.",
                    status_code=400,
                    details={"error": str(exc)},
                ) from exc

            indicator_map = {
                "net_profit_margin": (net_profit, revenue, "净利润率"),
                "current_ratio": (current_assets, current_liabilities, "流动比率"),
                "roe": (net_profit, equity, "ROE"),
            }

            for indicator_name, (numerator, denominator, label) in indicator_map.items():
                if denominator == 0:
                    if missing_value_strategy == "error":
                        raise AppError(
                            code=ErrorCode.MISSING_REQUIRED_SUBJECT,
                            message=f"Missing denominator for {indicator_name}.",
                            status_code=400,
                        )
                    warnings.append(f"{company}-{year}:{label} denominator missing")
                    value = np.nan
                else:
                    value = numerator / denominator

                metrics.append(
                    {
                        "company_name": company,
                        "year": int(year),
                        "indicator_name": indicator_name,
                        "indicator_value": value,
                        "details": json.dumps(
                            {
                                "numerator": numerator,
                                "denominator": denominator,
                                "label": label,
                            },
                            ensure_ascii=False,
                        ),
                    }
                )

    metrics_df = pd.DataFrame(metrics)
    return IndicatorResult(metrics=metrics_df, warnings=warnings)
