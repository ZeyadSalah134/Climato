"""PDF scientific analysis report generation.

The report is built with ReportLab from the stored, typed analysis response so
every number in the document is a real computed result.  The chart is drawn
from the returned trend-line points rather than being a decorative image.
"""

from __future__ import annotations

import io

from app.schemas.analysis import TrendAnalysisResponse

_BRAND = "#0F6B45"
_INK = "#12211C"


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}g}"


def build_pdf(response: TrendAnalysisResponse) -> bytes:
    try:
        from reportlab.graphics.charts.linecharts import HorizontalLineChart
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "PDF export requires the 'reportlab' package. Install it with 'pip install reportlab'."
        ) from exc

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"EarthTrend Analysis {response.analysis_id}",
        author="EarthTrend",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("ETitle", parent=styles["Title"], textColor=colors.HexColor(_BRAND), fontSize=20)
    h2 = ParagraphStyle("EHead", parent=styles["Heading2"], textColor=colors.HexColor(_BRAND))
    body = ParagraphStyle("EBody", parent=styles["BodyText"], leading=14)
    small = ParagraphStyle("ESmall", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)

    request = response.request
    provenance = response.provenance
    quality = response.quality

    story: list = []
    story.append(Paragraph("EarthTrend Scientific Analysis Report", h1))
    story.append(
        Paragraph(
            f"{provenance.variable_name} ({provenance.variable}) &mdash; "
            f"{request.location.name or 'Selected location'}",
            h2,
        )
    )
    story.append(Paragraph(f"Analysis ID: {response.analysis_id}", small))
    story.append(Paragraph(f"Generated: {response.created_at.isoformat()}", small))
    story.append(Spacer(1, 0.4 * cm))

    # --- metadata -------------------------------------------------------
    meta_rows = [
        ["Location", request.location.name or "unnamed"],
        ["Coordinates", f"{request.location.latitude:.4f}, {request.location.longitude:.4f}"],
        ["Variable", f"{provenance.variable_name} ({provenance.variable})"],
        ["Units", provenance.units],
        ["Provider", provenance.provider],
        ["Dataset", provenance.dataset],
        ["Product type", provenance.product_type.replace("_", " ")],
        ["Spatial resolution", provenance.spatial_resolution],
        ["Frequency", request.frequency],
        ["Requested period", f"{request.start_date} to {request.end_date}"],
        [
            "Analysed period",
            f"{quality.period_start} to {quality.period_end}"
            if quality.period_start
            else "n/a",
        ],
        ["Valid observations", str(quality.n_valid)],
        ["Missing observations", f"{quality.n_missing} ({quality.missing_pct:.1f}%)"],
        ["Retrieval mode", provenance.retrieval_mode],
        ["Seasonal adjustment", "applied" if response.seasonal and response.seasonal.applied else "not applied"],
        ["Engine version", provenance.engine_version],
    ]
    table = Table(meta_rows, colWidths=[4.5 * cm, 12 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5EE")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(_INK)),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BFD9CC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.6 * cm))

    # --- chart ----------------------------------------------------------
    if response.trend_line:
        story.append(Paragraph("Observed series and fitted trend", h2))
        chart = _build_chart(response)
        if chart is not None:
            story.append(chart)
        story.append(Spacer(1, 0.5 * cm))

    # --- statistics -----------------------------------------------------
    story.append(Paragraph("Statistical results", h2))
    stat_rows = [["Statistic", "Value"]]
    if response.ols is not None:
        ols = response.ols
        stat_rows += [
            ["OLS slope", f"{_fmt(ols.slope_per_year)} {provenance.units}/year"],
            ["OLS slope per decade", f"{_fmt(ols.slope_per_decade)} {provenance.units}/decade"],
            ["95% CI (slope)", f"[{_fmt(ols.confidence_interval_95[0])}, {_fmt(ols.confidence_interval_95[1])}]"],
            ["p-value", _fmt(ols.p_value)],
            ["R-squared", f"{ols.r_squared:.3f}"],
            ["Trend direction", ols.direction.replace("_", " ")],
            ["Significant (alpha)", "yes" if ols.significant else "no"],
        ]
    if response.mann_kendall is not None:
        mk = response.mann_kendall
        stat_rows += [
            ["Mann-Kendall tau", f"{mk.tau:.3f}"],
            ["Mann-Kendall Z", f"{mk.z:.3f}"],
            ["Mann-Kendall p-value", _fmt(mk.p_value)],
        ]
    if response.theil_sen is not None:
        ts = response.theil_sen
        stat_rows += [
            ["Theil-Sen slope", f"{_fmt(ts.slope_per_year)} {provenance.units}/year"],
            ["Theil-Sen 95% CI", f"[{_fmt(ts.confidence_interval_95[0])}, {_fmt(ts.confidence_interval_95[1])}]"],
        ]
    stat_table = Table(stat_rows, colWidths=[6 * cm, 10.5 * cm])
    stat_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F6B45")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BFD9CC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(stat_table)
    story.append(Spacer(1, 0.6 * cm))

    # --- interpretation -------------------------------------------------
    story.append(Paragraph("Interpretation", h2))
    story.append(Paragraph(response.interpretation.narrative, body))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(response.interpretation.significance_statement, body))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(response.interpretation.practical_note, body))
    story.append(Spacer(1, 0.4 * cm))

    # --- limitations ----------------------------------------------------
    story.append(Paragraph("Limitations and caveats", h2))
    for item in response.interpretation.limitations:
        story.append(Paragraph(f"&bull; {item}", body))

    if response.warnings:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Warnings", h2))
        for warning in response.warnings:
            story.append(Paragraph(f"[{warning.severity}] {warning.message}", body))

    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            "Data source: NASA POWER (NASA Langley Research Center). EarthTrend is an "
            "independent educational project submitted to the NASA Space Apps Challenge and "
            "is not affiliated with or endorsed by NASA.",
            small,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _build_chart(response: TrendAnalysisResponse):
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.lib import colors

    points = response.trend_line
    if len(points) < 2:
        return None

    observed = [p.observed if p.observed is not None else p.fitted for p in points]
    fitted = [p.fitted for p in points]
    upper = [p.upper if p.upper is not None else p.fitted for p in points]
    lower = [p.lower if p.lower is not None else p.fitted for p in points]

    drawing = Drawing(460, 220)
    chart = HorizontalLineChart()
    chart.x = 40
    chart.y = 30
    chart.height = 160
    chart.width = 400
    chart.data = [observed, fitted, upper, lower]
    chart.joinedLines = 1
    chart.lines[0].strokeColor = colors.HexColor("#0F6B45")
    chart.lines[0].strokeWidth = 0.8
    chart.lines[1].strokeColor = colors.HexColor("#F6B85E")
    chart.lines[1].strokeWidth = 1.6
    chart.lines[2].strokeColor = colors.HexColor("#B7D9C9")
    chart.lines[2].strokeWidth = 0.5
    chart.lines[3].strokeColor = colors.HexColor("#B7D9C9")
    chart.lines[3].strokeWidth = 0.5

    values = [v for v in (observed + fitted + upper + lower) if v is not None]
    chart.valueAxis.valueMin = min(values)
    chart.valueAxis.valueMax = max(values)
    chart.valueAxis.valueStep = (max(values) - min(values)) / 5 or 1
    chart.categoryAxis.labels.fontSize = 6
    chart.categoryAxis.labels.angle = 0
    step = max(1, len(points) // 8)
    chart.categoryAxis.categoryNames = [
        points[i].date.isoformat() if i % step == 0 else "" for i in range(len(points))
    ]
    drawing.add(chart)
    drawing.add(
        String(
            40,
            200,
            f"Green: observed  |  Amber: fitted OLS trend  |  Pale: 95% CI ({response.provenance.units})",
            fontSize=7,
            fillColor=colors.HexColor("#3B4A44"),
        )
    )
    return drawing
