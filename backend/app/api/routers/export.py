"""Export endpoints: CSV, JSON, and PDF."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.exports import build_csv, build_json, build_pdf
from app.schemas.analysis import CompareResponse, TrendAnalysisResponse
from app.services.analysis_service import analysis_service

router = APIRouter(tags=["export"])

# PNG chart export is performed client-side from the rendered chart so the
# pixel-accurate on-screen figure is preserved.
SUPPORTED_FORMATS = {"csv", "json", "pdf"}


@router.get("/export/{analysis_id}", summary="Export an analysis result")
async def export_analysis(
    analysis_id: str,
    format: str = Query(default="csv", pattern="^(csv|json|pdf)$"),
    kind: str = Query(default="trend", pattern="^(trend|compare)$"),
) -> Response:
    record = analysis_service.get_record(analysis_id)

    if record.kind == "compare":
        payload = CompareResponse.model_validate_json(record.payload)
        if format != "json":
            return Response(
                content=build_json(payload),
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="earthtrend_{analysis_id}.json"'},
            )
        return Response(
            content=build_json(payload),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="earthtrend_{analysis_id}.json"'},
        )

    response = TrendAnalysisResponse.model_validate_json(record.payload)

    if format == "csv":
        return Response(
            content=build_csv(response),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="earthtrend_{analysis_id}.csv"'},
        )
    if format == "json":
        return Response(
            content=build_json(response),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="earthtrend_{analysis_id}.json"'},
        )

    pdf_bytes = build_pdf(response)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="earthtrend_{analysis_id}.pdf"'},
    )
