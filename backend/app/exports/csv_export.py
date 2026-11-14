"""CSV export of analysed observations and fitted trend values."""

from __future__ import annotations

import csv
import io

from app.schemas.analysis import TrendAnalysisResponse


def build_csv(response: TrendAnalysisResponse) -> str:
    """Render the analysed series as CSV.

    Columns: date, observed_value, anomaly (when seasonal adjustment was
    applied), fitted_value, ci_lower, ci_upper.  The header records the
    variable, units, location, and provenance so the file is self-describing.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    request = response.request
    provenance = response.provenance
    writer.writerow(["# EarthTrend analysis export"])
    writer.writerow(["# analysis_id", response.analysis_id])
    writer.writerow(["# variable", f"{provenance.variable} ({provenance.variable_name})"])
    writer.writerow(["# units", provenance.units])
    writer.writerow(["# provider", provenance.provider])
    writer.writerow(["# dataset", provenance.dataset])
    writer.writerow(["# product_type", provenance.product_type])
    writer.writerow(["# location", request.location.name or "unnamed"])
    writer.writerow(["# latitude", request.location.latitude])
    writer.writerow(["# longitude", request.location.longitude])
    writer.writerow(["# frequency", request.frequency])
    writer.writerow(["# retrieval_mode", provenance.retrieval_mode])
    writer.writerow(["# engine_version", provenance.engine_version])
    writer.writerow(["# generated_at", response.created_at.isoformat()])
    if response.ols is not None:
        writer.writerow(["# ols_slope_per_year", response.ols.slope_per_year])
        writer.writerow(["# ols_slope_per_decade", response.ols.slope_per_decade])
        writer.writerow(["# ols_p_value", response.ols.p_value])
        writer.writerow(["# ols_r_squared", response.ols.r_squared])
        writer.writerow(["# ols_significant", response.ols.significant])
    writer.writerow([])

    seasonal_applied = bool(response.seasonal and response.seasonal.applied)
    header = ["date", "observed_value"]
    if seasonal_applied:
        header.append("anomaly")
    header += ["fitted_value", "ci_lower", "ci_upper"]
    writer.writerow(header)

    anomalies = {}
    if seasonal_applied:
        for record in response.observations:
            if "anomaly" in record:
                anomalies[record["date"]] = record["anomaly"]

    for point in response.trend_line:
        row = [point.date.isoformat(), point.observed]
        if seasonal_applied:
            row.append(anomalies.get(point.date.isoformat()))
        row += [point.fitted, point.lower, point.upper]
        writer.writerow(row)

    return buffer.getvalue()
