"""Environmental variable registry endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.errors import NotFoundError
from app.schemas.variables import (
    DiscoveryRequest,
    DiscoveryResponse,
    VariableInfo,
    VariableListResponse,
)
from app.services.discovery_service import recommend
from app.services.variable_registry import get_variable, list_variables, variables_by_category

router = APIRouter(tags=["variables"])


@router.get("/variables", response_model=VariableListResponse, summary="List environmental variables")
async def get_variables(
    include_planned: bool = Query(default=True, description="Include planned (not yet available) integrations"),
    category: str | None = Query(default=None),
    available_only: bool = Query(default=False),
) -> VariableListResponse:
    definitions = list_variables(include_planned=include_planned)
    if available_only:
        definitions = [d for d in definitions if d.status == "available"]
    if category:
        definitions = [d for d in definitions if d.category.lower() == category.lower()]
    items = [definition.to_schema() for definition in definitions]
    return VariableListResponse(items=items, total=len(items))


@router.get("/variables/categories", summary="Variables grouped by category")
async def get_categories() -> dict[str, list[str]]:
    grouped = variables_by_category()
    return {category: [d.id for d in definitions] for category, definitions in grouped.items()}


@router.get("/variables/{variable_id}", response_model=VariableInfo, summary="Variable detail")
async def get_variable_detail(variable_id: str) -> VariableInfo:
    definition = get_variable(variable_id)
    return definition.to_schema()


@router.post("/variables/discover", response_model=DiscoveryResponse, summary="Recommend variables")
async def discover_variables(request: DiscoveryRequest) -> DiscoveryResponse:
    """Rule-based investigation assistant.

    Maps a plain-language question to supported variables with an explicit
    rationale. No scientific finding is asserted.
    """
    return recommend(request.question)
