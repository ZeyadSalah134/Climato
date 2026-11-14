"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class AnalysisRecord(Base):
    """A stored trend or comparison analysis.

    Indexed columns support the analysis history listing while the complete
    typed response is preserved as JSON so exports are exact reproductions.
    """

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), index=True)

    variable: Mapped[str] = mapped_column(String(64), index=True)
    variable_name: Mapped[str] = mapped_column(String(128))

    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    frequency: Mapped[str] = mapped_column(String(16))

    direction: Mapped[str | None] = mapped_column(String(32), nullable=True)
    slope_per_year: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    significant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    retrieval_mode: Mapped[str] = mapped_column(String(16), default="live")

    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
