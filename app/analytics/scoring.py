from __future__ import annotations

import numpy as np
import pandas as pd

from app.risk.rules import RISK_RULES


def score_indicator(indicator_name: str, value: float) -> tuple[str, float]:
    rules = RISK_RULES.get(indicator_name, [])
    if value is None or np.isnan(value):
        return "unknown", np.nan

    for rule in rules:
        if value >= rule["min"]:
            return rule["level"], float(rule["score"])
    return "unknown", np.nan


def apply_scoring(metrics_df: pd.DataFrame) -> pd.DataFrame:
    metrics_df = metrics_df.copy()
    levels = []
    scores = []
    for _, row in metrics_df.iterrows():
        level, score = score_indicator(row["indicator_name"], row["indicator_value"])
        levels.append(level)
        scores.append(score)
    metrics_df["risk_level"] = levels
    metrics_df["risk_score"] = scores
    return metrics_df


def calculate_overall_risk(metrics_df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    results = []
    for (company, year), group in metrics_df.groupby(["company_name", "year"]):
        available = group.dropna(subset=["risk_score"])
        if available.empty:
            overall = np.nan
        else:
            weight_sum = 0.0
            weighted_scores = 0.0
            for _, row in available.iterrows():
                weight = weights.get(row["indicator_name"], 0.0)
                if weight <= 0:
                    continue
                weight_sum += weight
                weighted_scores += weight * float(row["risk_score"])
            overall = weighted_scores / weight_sum if weight_sum else np.nan
        results.append({"company_name": company, "year": int(year), "overall_risk_score": overall})
    return pd.DataFrame(results)
