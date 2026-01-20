from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    app_name: str = "py-data-processor-service"
    app_env: str = "local"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    max_upload_size_mb: int = 5
    json_max_depth: int = 20
    json_max_nodes: int = 20000
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


class UploadConstraints(BaseModel):
    max_bytes: int
    json_max_depth: int
    json_max_nodes: int


def get_settings() -> AppSettings:
    return AppSettings()
