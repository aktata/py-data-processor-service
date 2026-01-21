from __future__ import annotations

import pandas as pd

from app.analytics.indicators import calculate_indicators


def test_calculate_indicators() -> None:
    facts = pd.DataFrame(
        [
            {
                "company_name": "Alpha",
                "statement_type": "income_statement",
                "subject_path": "利润>净利润",
                "subject_l1": "利润",
                "subject_l2": "净利润",
                "subject_l3": "",
                "year": 2023,
                "amount": 2000,
            },
            {
                "company_name": "Alpha",
                "statement_type": "income_statement",
                "subject_path": "收入>营业收入",
                "subject_l1": "收入",
                "subject_l2": "营业收入",
                "subject_l3": "",
                "year": 2023,
                "amount": 10000,
            },
            {
                "company_name": "Alpha",
                "statement_type": "balance_sheet",
                "subject_path": "资产>流动资产",
                "subject_l1": "资产",
                "subject_l2": "流动资产",
                "subject_l3": "",
                "year": 2023,
                "amount": 5000,
            },
            {
                "company_name": "Alpha",
                "statement_type": "balance_sheet",
                "subject_path": "负债>流动负债",
                "subject_l1": "负债",
                "subject_l2": "流动负债",
                "subject_l3": "",
                "year": 2023,
                "amount": 2500,
            },
            {
                "company_name": "Alpha",
                "statement_type": "balance_sheet",
                "subject_path": "所有者权益",
                "subject_l1": "所有者权益",
                "subject_l2": "",
                "subject_l3": "",
                "year": 2023,
                "amount": 8000,
            },
        ]
    )

    result = calculate_indicators(facts)
    metrics = result.metrics
    net_profit_margin = metrics[metrics["indicator_name"] == "net_profit_margin"][
        "indicator_value"
    ].iloc[0]
    assert round(net_profit_margin, 2) == 0.2
