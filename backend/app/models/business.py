import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class BusinessStatus(enum.StrEnum):
    pending = "pending"
    researching = "researching"
    done = "done"
    failed = "failed"


class Business(Base):
    """A business from an upload, plus its research result."""

    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    status: Mapped[BusinessStatus] = mapped_column(
        Enum(BusinessStatus, name="business_status"), default=BusinessStatus.pending, index=True
    )

    # Input (business fields only)
    business_name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(500), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    country: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    # Research output
    final_url: Mapped[str | None] = mapped_column(String(500))
    site_status: Mapped[str | None] = mapped_column(String(120))
    industry: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text)
    services: Mapped[list | None] = mapped_column(JSON)
    size_estimate: Mapped[str | None] = mapped_column(String(60))
    gaps: Mapped[list | None] = mapped_column(JSON)
    offers: Mapped[list | None] = mapped_column(JSON)  # [{id, name, reason}]
    priority: Mapped[str | None] = mapped_column(String(10), index=True)
    outreach_angle: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(10))
    mode: Mapped[str | None] = mapped_column(String(20))
    pages_read: Mapped[list | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job = relationship("Job", back_populates="businesses")
