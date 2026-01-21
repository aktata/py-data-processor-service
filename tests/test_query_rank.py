from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.analytics.ranking import top_n_companies
from app.storage.repository import ingest_facts, query_metrics, replace_metrics


def test_query_and_rank(tmp_path: Path) -> None:
    facts = pd.DataFrame(
        [
            {
                "company_name": "Alpha",
                "statement_type": "income_statement",
                "category": "收入",
                "subject_path": "收入>营业收入",
                "subject_l1": "收入",
                "subject_l2": "营业收入",
                "subject_l3": "",
                "year": 2023,
                "amount": 10000,
            }
        ]
    )
    db_path = tmp_path / "finance.db"
    ingest_facts(str(db_path), facts)

    metrics = pd.DataFrame(
        [
            {
                "company_name": "Alpha",
                "year": 2023,
                "indicator_name": "net_profit_margin",
                "indicator_value": 0.2,
                "risk_level": "low",
                "risk_score": 10,
                "details": "{}",
            },
            {
                "company_name": "Beta",
                "year": 2023,
                "indicator_name": "net_profit_margin",
                "indicator_value": 0.1,
                "risk_level": "medium",
                "risk_score": 50,
                "details": "{}",
            },
        ]
    )
    overall = pd.DataFrame(
        [
            {"company_name": "Alpha", "year": 2023, "overall_risk_score": 10},
            {"company_name": "Beta", "year": 2023, "overall_risk_score": 50},
        ]
    )
    replace_metrics(str(db_path), metrics, overall)

    results = query_metrics(str(db_path), company="Alpha")
    assert len(results) == 1

    ranking = top_n_companies(metrics, "net_profit_margin", 2023, n=1)
    assert ranking.iloc[0]["company_name"] == "Alpha"
