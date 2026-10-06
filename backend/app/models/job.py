from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .user import utcnow


class Job(Base):
    """A job opening that resumes are screened against."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # Screening criteria; see app.ai.rubric.JobCriteria for the shape.
    criteria: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="jobs")  # noqa: F821
    candidates: Mapped[list["Candidate"]] = relationship(  # noqa: F821
        back_populates="job", cascade="all, delete-orphan"
    )
