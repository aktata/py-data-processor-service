from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "financial-risk-analysis-service"
    app_env: str = "local"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    input_dir: str = "data/input"
    output_dir: str = "data/output"
    db_path: str = "data/output/finance.db"
    missing_value_strategy: str = "warn"  # warn | error

    indicator_weights: dict[str, float] = {
        "net_profit_margin": 0.4,
        "current_ratio": 0.3,
        "roe": 0.3,
    }

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


def get_settings() -> AppSettings:
    return AppSettings()
