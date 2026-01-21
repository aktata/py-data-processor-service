from __future__ import annotations

import time
from typing import Any

import pandas as pd
from fastapi import APIRouter, Body, Request

from app.analytics.drilldown import drilldown_facts
from app.analytics.ranking import top_n_companies
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.response import success_response
from app.storage.repository import fetch_facts, fetch_metrics_df, query_metrics

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health(request: Request) -> Any:
    uptime = time.time() - request.app.state.start_time
    payload = {
        "status": "ok",
        "version": settings.app_version,
        "uptime_seconds": int(uptime),
    }
    return success_response(payload)


@router.post("/query")
async def query_metrics_api(
    company: str | None = Body(default=None),
    year: int | None = Body(default=None),
    indicator: str | None = Body(default=None),
) -> Any:
    data = query_metrics(settings.db_path, company, year, indicator)
    return success_response({"items": data})


@router.post("/rank")
async def rank_metrics_api(
    indicator: str = Body(...),
    year: int = Body(...),
    n: int = Body(default=5),
    order: str = Body(default="desc"),
) -> Any:
    metrics_df = fetch_metrics_df(settings.db_path)
    if metrics_df.empty:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="No metrics found. Run calc first.",
            status_code=400,
        )
    ranking = top_n_companies(metrics_df, indicator, year, n=n, order=order)
    return success_response({"items": ranking.to_dict(orient="records")})


@router.post("/drilldown")
async def drilldown_api(
    company: str = Body(...),
    year: int = Body(...),
    statement_type: str = Body(...),
    subject_prefix: str = Body(...),
) -> Any:
    facts_df = fetch_facts(settings.db_path)
    result = drilldown_facts(
        pd.DataFrame(facts_df), company, year, statement_type, subject_prefix
    )
    return success_response({"items": result.to_dict(orient="records")})
