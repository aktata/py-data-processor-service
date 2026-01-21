from __future__ import annotations

import pandas as pd


def drilldown_facts(
    facts_df: pd.DataFrame,
    company: str,
    year: int,
    statement_type: str,
    subject_prefix: str,
) -> pd.DataFrame:
    subset = facts_df[
        (facts_df["company_name"] == company)
        & (facts_df["year"] == year)
        & (facts_df["statement_type"] == statement_type)
    ]
    return subset[subset["subject_path"].str.startswith(subject_prefix)].copy()
