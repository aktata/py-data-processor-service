from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.reporting.excel_report import export_excel_report


def test_export_excel(tmp_path: Path) -> None:
    metrics = pd.DataFrame(
        [
            {
                "company_name": "Alpha",
                "year": 2023,
                "indicator_name": "net_profit_margin",
                "indicator_value": 0.2,
                "risk_level": "low",
                "risk_score": 10,
            }
        ]
    )
    ranking = metrics.copy()
    output_path = tmp_path / "report.xlsx"
    export_excel_report(metrics, ranking, None, output_path)
    assert output_path.exists()
