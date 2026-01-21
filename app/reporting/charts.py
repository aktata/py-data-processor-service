from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_trend(
    metrics_df: pd.DataFrame,
    company: str,
    indicator_names: list[str],
    output_path: Path,
) -> Path:
    company_df = metrics_df[metrics_df["company_name"] == company]
    plt.figure(figsize=(6, 3))
    for indicator in indicator_names:
        subset = company_df[company_df["indicator_name"] == indicator]
        plt.plot(subset["year"], subset["indicator_value"], marker="o", label=indicator)
    plt.title(f"{company} 关键指标趋势")
    plt.xlabel("年份")
    plt.ylabel("指标值")
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def plot_bar(
    metrics_df: pd.DataFrame,
    indicator: str,
    year: int,
    output_path: Path,
) -> Path:
    subset = metrics_df[
        (metrics_df["indicator_name"] == indicator) & (metrics_df["year"] == year)
    ]
    subset = subset.sort_values("indicator_value", ascending=False)
    plt.figure(figsize=(6, 3))
    plt.bar(subset["company_name"], subset["indicator_value"])
    plt.title(f"{year} {indicator} 排名")
    plt.xlabel("公司")
    plt.ylabel("指标值")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def plot_heatmap(metrics_df: pd.DataFrame, year: int, output_path: Path) -> Path:
    pivot = metrics_df[metrics_df["year"] == year].pivot(
        index="company_name", columns="indicator_name", values="risk_score"
    )
    plt.figure(figsize=(6, 3))
    plt.imshow(pivot, aspect="auto", cmap="Reds")
    plt.colorbar(label="风险分数")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
    plt.title(f"{year} 风险热力图")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path
