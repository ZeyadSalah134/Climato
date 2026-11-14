"""JSON export of a complete analysis result."""

from __future__ import annotations

import json

from app.schemas.analysis import CompareResponse, TrendAnalysisResponse


def build_json(response: TrendAnalysisResponse | CompareResponse) -> str:
    """Serialise the full typed response, preserving all provenance metadata."""
    return json.dumps(json.loads(response.model_dump_json()), indent=2)
