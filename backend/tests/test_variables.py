"""Variable registry and discovery assistant tests."""

from __future__ import annotations

import pytest

from app.core.errors import UnsupportedVariableError
from app.services.discovery_service import recommend
from app.services.variable_registry import (
    available_variable_ids,
    get_variable,
    list_variables,
)


def test_available_variables_present() -> None:
    ids = available_variable_ids()
    assert "T2M" in ids
    assert "PRECTOTCORR" in ids
    assert "RH2M" in ids
    assert "WS10M" in ids
    assert "ALLSKY_SFC_SW_DWN" in ids


def test_planned_variables_are_labelled() -> None:
    variables = list_variables(include_planned=True)
    planned = [v for v in variables if v.status == "planned_integration"]
    assert len(planned) >= 4
    assert all(v.id not in available_variable_ids() for v in planned)


def test_get_variable_unknown_raises() -> None:
    with pytest.raises(UnsupportedVariableError):
        get_variable("NOT_REAL")


def test_get_variable_planned_requires_available_flag() -> None:
    definition = get_variable("MODIS_NDVI")
    assert definition.status == "planned_integration"
    with pytest.raises(UnsupportedVariableError):
        get_variable("MODIS_NDVI", require_available=True)


def test_discovery_recommends_temperature() -> None:
    response = recommend("Is my region getting warmer?")
    ids = [rec.variable.id for rec in response.recommendations]
    assert ids[0] == "T2M"
    assert response.intent == "temperature_change"
    assert response.recommendations[0].relevance > 0


def test_discovery_recommends_precipitation() -> None:
    response = recommend("Is rainfall changing in my area?")
    ids = [rec.variable.id for rec in response.recommendations]
    assert "PRECTOTCORR" in ids


def test_discovery_handles_unmatched_question() -> None:
    response = recommend("Tell me something interesting")
    assert len(response.recommendations) == 3
    assert "do not" in response.note or "not" in response.note
