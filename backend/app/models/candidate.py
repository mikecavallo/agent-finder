from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .user import utcnow

CANDIDATE_STATUSES = ("new", "shortlisted", "contacted", "rejected")


class Candidate(Base):
    """A resume submitted for a job opening, with extracted data and its screening result."""

    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)

    # Extracted profile
    name: Mapped[str] = mapped_column(String(255), default="Unknown candidate")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    licenses: Mapped[list] = mapped_column(JSON, default=list)
    languages: Mapped[list] = mapped_column(JSON, default=list)
    years_sales: Mapped[float | None] = mapped_column(Float, nullable=True)
    years_customer_service: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")

    # Source
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text)

    # Screening result
    score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    breakdown: Mapped[list] = mapped_column(JSON, default=list)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    concerns: Mapped[list] = mapped_column(JSON, default=list)
    scored_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Recruiter workflow
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    outreach_draft: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    job: Mapped["Job"] = relationship(back_populates="candidates")  # noqa: F821
