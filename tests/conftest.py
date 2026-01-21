from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

YEARS = [2022, 2023]


def _balance_sheet(seed: int) -> pd.DataFrame:
    data = {
        "subject_l1": ["资产", "负债", "所有者权益"],
        "subject_l2": ["流动资产", "流动负债", ""],
        "subject_l3": ["货币资金", "短期借款", ""],
        "2022": [5000 + seed * 100, 3000 + seed * 50, 7000 + seed * 80],
        "2023": [5200 + seed * 100, 3200 + seed * 50, 7200 + seed * 80],
    }
    return pd.DataFrame(data)


def _income_statement(seed: int) -> pd.DataFrame:
    data = {
        "subject_l1": ["收入", "利润"],
        "subject_l2": ["营业收入", "净利润"],
        "subject_l3": ["", ""],
        "2022": [10000 + seed * 200, 1500 + seed * 30],
        "2023": [11000 + seed * 200, 1600 + seed * 30],
    }
    return pd.DataFrame(data)


def _cash_flow(seed: int) -> pd.DataFrame:
    data = {
        "subject_l1": ["经营活动"],
        "subject_l2": ["经营现金流"],
        "subject_l3": [""],
        "2022": [1200 + seed * 20],
        "2023": [1300 + seed * 20],
    }
    return pd.DataFrame(data)


def create_company_excel(path: Path, seed: int) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        _balance_sheet(seed).to_excel(writer, sheet_name="资产负债表", index=False)
        _income_statement(seed).to_excel(writer, sheet_name="利润表", index=False)
        _cash_flow(seed).to_excel(writer, sheet_name="现金流量表", index=False)


@pytest.fixture()
def demo_input_dir(tmp_path: Path) -> Path:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    create_company_excel(input_dir / "Alpha.xlsx", 1)
    create_company_excel(input_dir / "Beta.xlsx", 2)
    return input_dir
