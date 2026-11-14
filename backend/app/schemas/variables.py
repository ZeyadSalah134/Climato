"""Variable registry schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VariableStatus = Literal["available", "planned_integration", "deprecated"]


class VariableInfo(BaseModel):
    id: str = Field(..., description="Stable identifier, e.g. T2M")
    code: str = Field(..., description="Provider parameter code, e.g. T2M")
    scientific_name: str
    display_name: str
    description: str
    units: str
    category: str
    provider: str
    dataset: str
    product_type: Literal[
        "satellite_observation",
        "model_estimate",
        "reanalysis",
        "reference_dataset",
    ]
    temporal_coverage: str
    spatial_coverage: str
    spatial_resolution: str
    frequencies: list[str]
    source_documentation: str
    limitations: list[str]
    status: VariableStatus = "available"
    supported_by: str = "NASA_POWER"
    color: str = "#21C77A"
    sample_value: float | None = None


class VariableListResponse(BaseModel):
    items: list[VariableInfo]
    total: int


class DiscoveryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


class DiscoveryRecommendation(BaseModel):
    variable: VariableInfo
    relevance: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    example_question: str


class DiscoveryResponse(BaseModel):
    question: str
    intent: str
    recommendations: list[DiscoveryRecommendation]
    suggested_investigations: list[str]
    note: str
