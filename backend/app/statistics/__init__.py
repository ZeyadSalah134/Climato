"""Statistical analysis engine."""

from app.statistics.engine import ENGINE_VERSION, AnalysisComputation, run_analysis
from app.statistics.types import Series

__all__ = ["AnalysisComputation", "ENGINE_VERSION", "Series", "run_analysis"]
