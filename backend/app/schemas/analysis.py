"""Statistical analysis request/response schemas.

These models are the contract between the statistical engine and every
consumer (API routers, export services, frontend TypeScript client).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import DataProvenance, GeoPoint, Warning

MethodName = Literal["ols", "mann_kendall", "theil_sen"]
TrendDirection = Literal["increasing", "decreasing", "no_detectable_trend"]
Significance = Literal["significant", "not_significant", "insufficient_data"]


# --------------------------------------------------------------------------
# Requests
# --------------------------------------------------------------------------
class TrendRequest(BaseModel):
    variable: str = Field(..., examples=["T2M"])
    source: str = Field(default="NASA_POWER")
    location: GeoPoint
    start_date: date
    end_date: date
    frequency: Literal["monthly", "daily"] = "monthly"
    methods: list[MethodName] = Field(default_factory=lambda: ["ols", "mann_kendall", "theil_sen"])
    seasonal_adjustment: bool = False
    alpha: float = Field(default=0.05, gt=0.0, lt=1.0)

    @model_validator(mode="after")
    def _check_range(self) -> "TrendRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        if not self.methods:
            raise ValueError("at least one statistical method is required")
        return self


class CompareRequest(BaseModel):
    variable: str
    source: str = "NASA_POWER"
    location_a: GeoPoint
    location_b: GeoPoint
    start_date: date
    end_date: date
    frequency: Literal["monthly", "daily"] = "monthly"
    seasonal_adjustment: bool = False
    alpha: float = Field(default=0.05, gt=0.0, lt=1.0)
    normalize: bool = False

    @model_validator(mode="after")
    def _check_range(self) -> "CompareRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


# --------------------------------------------------------------------------
# Statistical building blocks
# --------------------------------------------------------------------------
class LinearTrendResult(BaseModel):
    method: Literal["ols"] = "ols"
    model: str = "y(t) = b0 + b1 * t"
    slope_per_year: float
    slope_per_decade: float
    intercept: float
    standard_error: float
    p_value: float
    r_squared: float
    adjusted_r_squared: float
    confidence_interval_95: tuple[float, float]
    confidence_interval_95_per_decade: tuple[float, float]
    t_statistic: float
    degrees_of_freedom: int
    direction: TrendDirection
    significant: bool
    significance: Significance
    n_observations: int
    units_per_year: str
    units_per_decade: str


class MannKendallResult(BaseModel):
    method: Literal["mann_kendall"] = "mann_kendall"
    trend: TrendDirection
    tau: float
    s: float
    z: float
    p_value: float
    variance_s: float
    significant: bool
    significance: Significance
    n_observations: int
    autocorrelation_risk: bool = False
    note: str


class TheilSenResult(BaseModel):
    method: Literal["theil_sen"] = "theil_sen"
    slope_per_year: float
    slope_per_decade: float
    intercept: float
    confidence_interval_95: tuple[float, float]
    confidence_interval_95_per_decade: tuple[float, float]
    direction: TrendDirection
    n_observations: int
    units_per_year: str
    units_per_decade: str


class MonthlyClimatology(BaseModel):
    month: int = Field(..., ge=1, le=12)
    month_name: str
    mean: float
    count: int


class SeasonalResult(BaseModel):
    applied: bool
    baseline_start: date | None = None
    baseline_end: date | None = None
    climatology: list[MonthlyClimatology] = Field(default_factory=list)
    note: str = ""


class QualityCheck(BaseModel):
    name: str
    status: Literal["pass", "warning", "fail"]
    message: str


class DataQuality(BaseModel):
    n_valid: int
    n_expected: int
    n_missing: int
    missing_pct: float
    period_start: date | None = None
    period_end: date | None = None
    period_years: float = 0.0
    is_constant: bool = False
    lag1_autocorrelation: float | None = None
    autocorrelation_warning: bool = False
    irregular_sampling: bool = False
    min_observations_required: int
    sufficient: bool
    checks: list[QualityCheck] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TrendLinePoint(BaseModel):
    date: date
    observed: float | None = None
    fitted: float
    lower: float | None = None
    upper: float | None = None


class DistributionBin(BaseModel):
    label: str
    count: int


class Interpretation(BaseModel):
    headline: str
    narrative: str
    significance_statement: str
    practical_note: str
    limitations: list[str]


class TrendAnalysisResponse(BaseModel):
    analysis_id: str
    kind: Literal["trend"] = "trend"
    request: TrendRequest
    provenance: DataProvenance
    quality: DataQuality
    observations: list[dict] = Field(default_factory=list)
    trend_line: list[TrendLinePoint] = Field(default_factory=list)
    ols: LinearTrendResult | None = None
    mann_kendall: MannKendallResult | None = None
    theil_sen: TheilSenResult | None = None
    seasonal: SeasonalResult | None = None
    distribution: list[DistributionBin] = Field(default_factory=list)
    interpretation: Interpretation
    warnings: list[Warning] = Field(default_factory=list)
    created_at: datetime
    cached: bool = False


class ComparisonSummary(BaseModel):
    descriptive_only: bool = True
    slope_difference_per_year: float | None = None
    slope_difference_per_decade: float | None = None
    direction_a: TrendDirection | None = None
    direction_b: TrendDirection | None = None
    aligned_observations: int = 0
    normalized: bool = False
    summary: str
    note: str


class CompareResponse(BaseModel):
    comparison_id: str
    kind: Literal["compare"] = "compare"
    request: CompareRequest
    location_a: TrendAnalysisResponse
    location_b: TrendAnalysisResponse
    comparison: ComparisonSummary
    created_at: datetime


class AnalysisHistoryItem(BaseModel):
    analysis_id: str
    kind: str
    variable: str
    variable_name: str
    location_name: str | None
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    frequency: str
    direction: str | None
    slope_per_year: float | None
    p_value: float | None
    significant: bool | None
    created_at: datetime
