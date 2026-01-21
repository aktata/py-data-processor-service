from __future__ import annotations

import pandas as pd

from app.analytics.scoring import apply_scoring, calculate_overall_risk


def test_scoring_and_overall() -> None:
    metrics = pd.DataFrame(
        [
            {
                "company_name": "Alpha",
                "year": 2023,
                "indicator_name": "net_profit_margin",
                "indicator_value": 0.25,
            },
            {
                "company_name": "Alpha",
                "year": 2023,
                "indicator_name": "current_ratio",
                "indicator_value": 1.2,
            },
            {
                "company_name": "Alpha",
                "year": 2023,
                "indicator_name": "roe",
                "indicator_value": 0.1,
            },
        ]
    )

    scored = apply_scoring(metrics)
    assert "risk_level" in scored.columns

    overall = calculate_overall_risk(
        scored, {"net_profit_margin": 0.4, "current_ratio": 0.3, "roe": 0.3}
    )
    assert overall["overall_risk_score"].iloc[0] > 0
