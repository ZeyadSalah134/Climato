"""Rule-based environmental investigation assistant.

Maps a natural-language question to supported environmental variables using
keyword matching over the variable registry.  The assistant is deterministic
and fully offline: it recommends variables and explains *why*, but it never
asserts scientific findings.  Any external LLM integration would be optional
and would have to ground its output in computed results.
"""

from __future__ import annotations

import re

from app.schemas.variables import (
    DiscoveryRecommendation,
    DiscoveryResponse,
    VariableInfo,
)
from app.services.variable_registry import POWER_VARIABLES, VariableDefinition

INTENTS: list[tuple[str, list[str]]] = [
    ("temperature_change", ["warm", "warmer", "warming", "temperature", "hot", "heat", "cooler", "colder", "thermal"]),
    ("precipitation_change", ["rain", "rainfall", "precip", "wet", "wetter", "dry", "drier", "drought", "monsoon"]),
    ("humidity_change", ["humid", "humidity", "moisture", "arid", "aridity", "vapour", "vapor"]),
    ("wind_change", ["wind", "windy", "gust", "breeze", "circulation"]),
    ("solar_change", ["solar", "sun", "sunshine", "radiation", "irradiance", "cloud", "photovoltaic", "energy"]),
    ("comparison", ["compare", "versus", "vs", "difference", "between", "two cities"]),
]


def _detect_intent(question: str) -> str:
    lowered = question.lower()
    best = ("general", 0)
    for intent, keywords in INTENTS:
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best[1]:
            best = (intent, score)
    return best[0]


def _score_variable(question: str, definition: VariableDefinition) -> float:
    lowered = question.lower()
    tokens = set(re.findall(r"[a-z]+", lowered))
    hits = 0
    for keyword in definition.keywords:
        if keyword in tokens or keyword in lowered:
            hits += 1
    if definition.display_name.lower() in lowered:
        hits += 3
    if definition.id.lower() in lowered:
        hits += 3
    if hits == 0:
        return 0.0
    return min(1.0, hits / 3.0)


def _rationale(definition: VariableDefinition) -> str:
    return (
        f"{definition.display_name} ({definition.id}) measures {definition.scientific_name.lower()} "
        f"in {definition.units}. It is the closest supported indicator for this question and is "
        f"available through {definition.provider}."
    )


def recommend(question: str, limit: int = 3) -> DiscoveryResponse:
    intent = _detect_intent(question)
    scored: list[tuple[float, VariableDefinition]] = []
    for definition in POWER_VARIABLES:
        score = _score_variable(question, definition)
        if score > 0:
            scored.append((score, definition))

    scored.sort(key=lambda item: item[0], reverse=True)

    if not scored:
        # No keyword matched: return the three most broadly useful indicators.
        scored = [(0.35, definition) for definition in POWER_VARIABLES[:3]]

    recommendations = [
        DiscoveryRecommendation(
            variable=definition.to_schema(),
            relevance=round(score, 2),
            rationale=_rationale(definition),
            example_question=_example_for(definition),
        )
        for score, definition in scored[:limit]
    ]

    suggested = [
        "Is my region getting warmer?",
        "Is rainfall changing in the Amazon Basin?",
        "Is the local environment becoming drier?",
        "How does the climate in two cities compare?",
    ]

    return DiscoveryResponse(
        question=question,
        intent=intent,
        recommendations=recommendations,
        suggested_investigations=suggested,
        note=(
            "Recommendations are produced by a transparent keyword-matching rule set over the "
            "supported variable registry. They suggest which variable to analyse; they do not "
            "contain or imply any scientific finding."
        ),
    )


def _example_for(definition: VariableDefinition) -> str:
    mapping = {
        "T2M": "Is my region getting warmer?",
        "PRECTOTCORR": "Is rainfall changing in my region?",
        "RH2M": "Is the local environment becoming drier?",
        "WS10M": "Are wind conditions changing where I live?",
        "ALLSKY_SFC_SW_DWN": "Is solar radiation changing at this location?",
    }
    return mapping.get(definition.id, f"How is {definition.display_name.lower()} changing?")


def variable_to_info(definition: VariableDefinition) -> VariableInfo:
    return definition.to_schema()
