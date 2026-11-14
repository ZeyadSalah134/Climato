"""Statistical analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_allow_demo, rate_limit
from app.schemas.analysis import (
    AnalysisHistoryItem,
    CompareRequest,
    CompareResponse,
    TrendAnalysisResponse,
    TrendRequest,
)
from app.schemas.common import Paginated
from app.services.analysis_service import analysis_service

router = APIRouter(tags=["analysis"], dependencies=[Depends(rate_limit)])


@router.post("/analysis/trend", response_model=TrendAnalysisResponse, summary="Run a trend analysis")
async def run_trend(
    request: TrendRequest,
    allow_demo: bool = Depends(get_allow_demo),
) -> TrendAnalysisResponse:
    """Retrieve NASA data for a coordinate and compute trend statistics.

    Returns the observations, fitted trend line with confidence band, OLS /
    Mann-Kendall / Theil-Sen results, data-quality assessment, provenance, and
    a generated interpretation.
    """
    return await analysis_service.run_trend(request, allow_demo=allow_demo)


@router.post("/analysis/compare", response_model=CompareResponse, summary="Compare two regions")
async def run_compare(
    request: CompareRequest,
    allow_demo: bool = Depends(get_allow_demo),
) -> CompareResponse:
    """Run two independent trend analyses and describe the difference.

    The comparison is descriptive: no formal test of slope difference is applied.
    """
    return await analysis_service.run_compare(request, allow_demo=allow_demo)


@router.get("/analysis/history", response_model=Paginated[AnalysisHistoryItem], summary="Analysis history")
async def analysis_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Paginated[AnalysisHistoryItem]:
    items, total = analysis_service.history(limit=limit, offset=offset)
    return Paginated[AnalysisHistoryItem](items=items, total=total, limit=limit, offset=offset)


@router.get("/analysis/{analysis_id}", response_model=TrendAnalysisResponse, summary="Retrieve an analysis")
async def get_analysis(analysis_id: str) -> TrendAnalysisResponse:
    return analysis_service.get(analysis_id)
