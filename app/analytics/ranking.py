from __future__ import annotations

import pandas as pd


def top_n_companies(
    metrics_df: pd.DataFrame,
    indicator: str,
    year: int,
    n: int = 5,
    order: str = "desc",
) -> pd.DataFrame:
    subset = metrics_df[
        (metrics_df["indicator_name"] == indicator) & (metrics_df["year"] == year)
    ].copy()
    subset = subset.dropna(subset=["indicator_value"])
    ascending = order == "asc"
    subset = subset.sort_values("indicator_value", ascending=ascending)
    return subset.head(n)
