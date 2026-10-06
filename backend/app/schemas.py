"""Request and response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .ai.rubric import CriterionResult, JobCriteria

Status = Literal["new", "shortlisted", "contacted", "rejected"]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JobIn(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    location: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=20_000)
    criteria: JobCriteria = Field(default_factory=JobCriteria)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=20_000)
    criteria: JobCriteria | None = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    location: str
    description: str
    criteria: JobCriteria
    created_at: datetime
    candidate_count: int = 0
    shortlisted_count: int = 0


class CandidateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    rank: int | None = None
    name: str
    email: str | None
    location: str | None
    current_title: str | None
    licenses: list[str]
    languages: list[str]
    years_sales: float | None
    score: float | None
    status: Status
    scored_by: str | None
    source_filename: str | None
    created_at: datetime


class CandidateOut(CandidateSummary):
    phone: str | None
    years_customer_service: float | None
    summary: str
    breakdown: list[CriterionResult]
    strengths: list[str]
    concerns: list[str]
    scored_at: datetime | None
    notes: str
    outreach_draft: str | None
    resume_text: str
    updated_at: datetime


class CandidateUpdate(BaseModel):
    status: Status | None = None
    notes: str | None = Field(default=None, max_length=10_000)


class PastedResume(BaseModel):
    text: str = Field(min_length=1, max_length=60_000)
    label: str | None = Field(default=None, max_length=255)


class UploadError(BaseModel):
    filename: str
    detail: str


class UploadResult(BaseModel):
    created: list[CandidateSummary]
    errors: list[UploadError]


class OutreachRequest(BaseModel):
    recruiter_name: str = Field(min_length=1, max_length=120)


class HealthOut(BaseModel):
    status: str
    provider: str
    demo_mode: bool
    version: str
