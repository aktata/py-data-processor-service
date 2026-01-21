from __future__ import annotations

from pathlib import Path

import pandas as pd

COMPANIES = ["星河科技", "海岭能源", "远航制造"]
YEARS = [2021, 2022, 2023]


def build_balance_sheet(seed: int) -> pd.DataFrame:
    data = {
        "subject_l1": ["资产", "资产", "负债", "负债", "所有者权益"],
        "subject_l2": ["流动资产", "非流动资产", "流动负债", "非流动负债", ""],
        "subject_l3": ["货币资金", "固定资产", "短期借款", "长期借款", ""],
    }
    for year in YEARS:
        data[str(year)] = [
            5000 + seed * 200 + (year - 2021) * 100,
            12000 + seed * 300 + (year - 2021) * 200,
            4000 + seed * 150 + (year - 2021) * 80,
            5000 + seed * 180 + (year - 2021) * 120,
            8000 + seed * 220 + (year - 2021) * 150,
        ]
    return pd.DataFrame(data)


def build_income_statement(seed: int) -> pd.DataFrame:
    data = {
        "subject_l1": ["收入", "成本", "费用", "利润"],
        "subject_l2": ["营业收入", "营业成本", "销售费用", "净利润"],
        "subject_l3": ["", "", "", ""],
    }
    for year in YEARS:
        revenue = 20000 + seed * 500 + (year - 2021) * 600
        cost = 12000 + seed * 300 + (year - 2021) * 400
        expense = 2000 + seed * 100 + (year - 2021) * 80
        net_profit = revenue - cost - expense
        data[str(year)] = [revenue, cost, expense, net_profit]
    return pd.DataFrame(data)


def build_cash_flow(seed: int) -> pd.DataFrame:
    data = {
        "subject_l1": ["经营活动", "投资活动", "筹资活动"],
        "subject_l2": ["经营现金流", "投资现金流", "筹资现金流"],
        "subject_l3": ["", "", ""],
    }
    for year in YEARS:
        data[str(year)] = [
            3000 + seed * 120 + (year - 2021) * 90,
            -1500 - seed * 80 - (year - 2021) * 50,
            800 + seed * 60 + (year - 2021) * 30,
        ]
    return pd.DataFrame(data)


def main() -> None:
    output_dir = Path("data/input")
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, company in enumerate(COMPANIES, start=1):
        path = output_dir / f"{company}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            build_balance_sheet(idx).to_excel(writer, sheet_name="资产负债表", index=False)
            build_income_statement(idx).to_excel(writer, sheet_name="利润表", index=False)
            build_cash_flow(idx).to_excel(writer, sheet_name="现金流量表", index=False)
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
