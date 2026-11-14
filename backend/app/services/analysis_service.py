"""Analysis orchestration service.

Combines retrieval, statistics, provenance, persistence, and interpretation
into the typed responses exposed by the API.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func, select

from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.models.analysis import AnalysisRecord
from app.models.database import session_scope
from app.schemas.analysis import (
    AnalysisHistoryItem,
    ComparisonSummary,
    CompareRequest,
    CompareResponse,
    TrendAnalysisResponse,
    TrendRequest,
)
from app.schemas.common import DataProvenance
from app.services.timeseries_service import TimeSeriesService, timeseries_service
from app.services.variable_registry import get_variable
from app.statistics import run_analysis

logger = get_logger(__name__)


class AnalysisService:
    def __init__(self, timeseries: TimeSeriesService | None = None) -> None:
        self.timeseries = timeseries or timeseries_service

    # -- trend -------------------------------------------------------------
    async def run_trend(self, request: TrendRequest, *, allow_demo: bool = True) -> TrendAnalysisResponse:
        definition = get_variable(request.variable, require_available=True)

        bundle = await self.timeseries.get_series(
            variable=request.variable,
            latitude=request.location.latitude,
            longitude=request.location.longitude,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            allow_demo=allow_demo,
        )

        computation = run_analysis(
            bundle.series,
            methods=list(request.methods),
            alpha=request.alpha,
            seasonal_adjustment=request.seasonal_adjustment,
            n_missing=len(bundle.provider_series.missing),
            requested_start=request.start_date,
            requested_end=request.end_date,
            provider_notes=bundle.warnings,
            units=bundle.provider_series.units or definition.units,
        )

        provenance = self._build_provenance(
            definition=definition,
            request=request,
            bundle=bundle,
            computation=computation,
        )

        analysis_id = uuid.uuid4().hex
        response = TrendAnalysisResponse(
            analysis_id=analysis_id,
            request=request,
            provenance=provenance,
            quality=computation.quality,
            observations=computation.observations,
            trend_line=computation.trend_line,
            ols=computation.ols,
            mann_kendall=computation.mann_kendall,
            theil_sen=computation.theil_sen,
            seasonal=computation.seasonal,
            distribution=computation.distribution,
            interpretation=computation.interpretation,
            warnings=computation.warnings,
            created_at=datetime.now(timezone.utc),
        )

        self._persist_trend(response)
        return response

    # -- compare -----------------------------------------------------------
    async def run_compare(self, request: CompareRequest, *, allow_demo: bool = True) -> CompareResponse:
        trend_a = await self.run_trend(
            TrendRequest(
                variable=request.variable,
                source=request.source,
                location=request.location_a,
                start_date=request.start_date,
                end_date=request.end_date,
                frequency=request.frequency,
                seasonal_adjustment=request.seasonal_adjustment,
                alpha=request.alpha,
            ),
            allow_demo=allow_demo,
        )
        trend_b = await self.run_trend(
            TrendRequest(
                variable=request.variable,
                source=request.source,
                location=request.location_b,
                start_date=request.start_date,
                end_date=request.end_date,
                frequency=request.frequency,
                seasonal_adjustment=request.seasonal_adjustment,
                alpha=request.alpha,
            ),
            allow_demo=allow_demo,
        )

        comparison = self._build_comparison(trend_a, trend_b, normalized=request.normalize)
        comparison_id = uuid.uuid4().hex
        response = CompareResponse(
            comparison_id=comparison_id,
            request=request,
            location_a=trend_a,
            location_b=trend_b,
            comparison=comparison,
            created_at=datetime.now(timezone.utc),
        )
        self._persist_compare(response)
        return response

    # -- retrieval ---------------------------------------------------------
    def get(self, analysis_id: str) -> TrendAnalysisResponse:
        with session_scope() as session:
            record = session.get(AnalysisRecord, analysis_id)
            if record is None:
                raise NotFoundError(f"No analysis found with id '{analysis_id}'.")
            payload = record.payload
        return TrendAnalysisResponse.model_validate_json(payload)

    def get_record(self, analysis_id: str) -> AnalysisRecord:
        with session_scope() as session:
            record = session.get(AnalysisRecord, analysis_id)
            if record is None:
                raise NotFoundError(f"No analysis found with id '{analysis_id}'.")
            session.expunge(record)
        return record

    def history(self, *, limit: int = 20, offset: int = 0) -> tuple[list[AnalysisHistoryItem], int]:
        with session_scope() as session:
            total = session.scalar(select(func.count()).select_from(AnalysisRecord)) or 0
            rows = (
                session.execute(
                    select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(limit).offset(offset)
                )
                .scalars()
                .all()
            )
        items = [
            AnalysisHistoryItem(
                analysis_id=row.id,
                kind=row.kind,
                variable=row.variable,
                variable_name=row.variable_name,
                location_name=row.location_name,
                latitude=row.latitude,
                longitude=row.longitude,
                start_date=row.start_date,
                end_date=row.end_date,
                frequency=row.frequency,
                direction=row.direction,
                slope_per_year=row.slope_per_year,
                p_value=row.p_value,
                significant=row.significant,
                created_at=row.created_at,
            )
            for row in rows
        ]
        return items, total

    # -- helpers -----------------------------------------------------------
    def _build_provenance(self, *, definition, request: TrendRequest, bundle, computation) -> DataProvenance:
        provider_series = bundle.provider_series
        quality = computation.quality
        return DataProvenance(
            variable=definition.id,
            variable_name=definition.display_name,
            units=provider_series.units or definition.units,
            provider=definition.provider,
            dataset=definition.dataset,
            product_type=definition.product_type,  # type: ignore[arg-type]
            spatial_resolution=definition.spatial_resolution,
            source_url=definition.source_documentation,
            request_params={
                "variable": request.variable,
                "source": request.source,
                "latitude": request.location.latitude,
                "longitude": request.location.longitude,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "frequency": request.frequency,
                "seasonal_adjustment": request.seasonal_adjustment,
                "alpha": request.alpha,
                "provider_request": provider_series.request_params,
                "provider_url": provider_series.request_url,
                "provider_api_version": provider_series.api_version,
            },
            requested_start=request.start_date.isoformat(),
            requested_end=request.end_date.isoformat(),
            analyzed_start=quality.period_start.isoformat() if quality else None,
            analyzed_end=quality.period_end.isoformat() if quality else None,
            frequency=request.frequency,
            retrieval_mode=bundle.retrieval_mode,  # type: ignore[arg-type]
            retrieved_at=datetime.now(timezone.utc),
            engine_version=settings.analysis_engine_version,
        )

    def _build_comparison(
        self,
        trend_a: TrendAnalysisResponse,
        trend_b: TrendAnalysisResponse,
        *,
        normalized: bool,
    ) -> ComparisonSummary:
        slope_a = trend_a.ols.slope_per_year if trend_a.ols else None
        slope_b = trend_b.ols.slope_per_year if trend_b.ols else None
        difference = None
        difference_decade = None
        if slope_a is not None and slope_b is not None:
            difference = slope_a - slope_b
            difference_decade = difference * 10.0

        aligned = min(
            len(trend_a.observations),
            len(trend_b.observations),
        )

        direction_a = trend_a.ols.direction if trend_a.ols else None
        direction_b = trend_b.ols.direction if trend_b.ols else None

        if slope_a is None or slope_b is None:
            summary = (
                "One or both locations did not produce a trend estimate; a descriptive "
                "comparison could not be formed."
            )
        else:
            summary = (
                f"Location A shows a {direction_a.replace('_', ' ') if direction_a else 'n/a'} "
                f"trend of {slope_a:.4g} {trend_a.provenance.units}/year while Location B shows a "
                f"{direction_b.replace('_', ' ') if direction_b else 'n/a'} trend of "
                f"{slope_b:.4g} {trend_b.provenance.units}/year. The observed slope difference "
                f"(A minus B) is {difference:.4g} {trend_a.provenance.units}/year."
            )

        return ComparisonSummary(
            descriptive_only=True,
            slope_difference_per_year=difference,
            slope_difference_per_decade=difference_decade,
            direction_a=direction_a,
            direction_b=direction_b,
            aligned_observations=aligned,
            normalized=normalized,
            summary=summary,
            note=(
                "This comparison is descriptive. The two trends were estimated independently "
                "and no formal test of the difference between slopes has been applied, so the "
                "difference should not be described as statistically significant."
            ),
        )

    # -- persistence -------------------------------------------------------
    def _persist_trend(self, response: TrendAnalysisResponse) -> None:
        record = AnalysisRecord(
            id=response.analysis_id,
            kind="trend",
            variable=response.provenance.variable,
            variable_name=response.provenance.variable_name,
            location_name=response.request.location.name,
            latitude=response.request.location.latitude,
            longitude=response.request.location.longitude,
            start_date=response.request.start_date,
            end_date=response.request.end_date,
            frequency=response.request.frequency,
            direction=response.ols.direction if response.ols else None,
            slope_per_year=response.ols.slope_per_year if response.ols else None,
            p_value=response.ols.p_value if response.ols else None,
            significant=response.ols.significant if response.ols else None,
            retrieval_mode=response.provenance.retrieval_mode,
            payload=response.model_dump_json(),
        )
        try:
            with session_scope() as session:
                session.add(record)
        except Exception as exc:  # pragma: no cover - persistence should not break analysis
            logger.error("Failed to persist analysis %s: %s", response.analysis_id, exc)

    def _persist_compare(self, response: CompareResponse) -> None:
        record = AnalysisRecord(
            id=response.comparison_id,
            kind="compare",
            variable=response.location_a.provenance.variable,
            variable_name=response.location_a.provenance.variable_name,
            location_name=(
                f"{response.request.location_a.name or 'A'} vs {response.request.location_b.name or 'B'}"
            ),
            latitude=response.request.location_a.latitude,
            longitude=response.request.location_a.longitude,
            start_date=response.request.start_date,
            end_date=response.request.end_date,
            frequency=response.request.frequency,
            direction=response.comparison.direction_a,
            slope_per_year=response.comparison.slope_difference_per_year,
            p_value=response.location_a.ols.p_value if response.location_a.ols else None,
            significant=None,
            retrieval_mode=response.location_a.provenance.retrieval_mode,
            payload=response.model_dump_json(),
        )
        try:
            with session_scope() as session:
                session.add(record)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to persist comparison %s: %s", response.comparison_id, exc)


analysis_service = AnalysisService()


def load_payload(record: AnalysisRecord) -> dict:
    return json.loads(record.payload)
