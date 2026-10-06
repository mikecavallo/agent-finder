"""Glue between the API layer, the LLM providers and the database."""

import asyncio
from datetime import datetime, timezone

from .ai.providers import JobContext, ProviderError, ScoringProvider, ScreeningResult
from .ai.rubric import JobCriteria, aggregate
from .models import Candidate, Job


def job_context(job: Job) -> JobContext:
    return JobContext(
        title=job.title,
        location=job.location or "",
        description=job.description or "",
        criteria=JobCriteria.model_validate(job.criteria or {}),
    )


def apply_result(candidate: Candidate, result: ScreeningResult, ctx: JobContext) -> None:
    p = result.profile
    candidate.name = p.name or "Unknown candidate"
    candidate.email = p.email
    candidate.phone = p.phone
    candidate.location = p.location
    candidate.current_title = p.current_title
    candidate.licenses = list(p.licenses)
    candidate.languages = list(p.languages)
    candidate.years_sales = p.years_sales
    candidate.years_customer_service = p.years_customer_service
    candidate.summary = p.summary or ""

    weights = ctx.criteria.effective_weights(ctx.location)
    total, breakdown = aggregate(result.assessments, weights)
    candidate.score = total
    candidate.breakdown = [item.model_dump() for item in breakdown]
    candidate.strengths = list(result.strengths)
    candidate.concerns = list(result.concerns)
    candidate.scored_by = result.scored_by
    candidate.scored_at = datetime.now(timezone.utc)


async def screen_many(
    provider: ScoringProvider, texts: list[str], ctx: JobContext, concurrency: int
) -> list[ScreeningResult | ProviderError]:
    """Screen several resumes concurrently, returning a result or error per input."""
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def one(text: str):
        async with semaphore:
            try:
                return await provider.screen(text, ctx)
            except ProviderError as exc:
                return exc

    return await asyncio.gather(*(one(t) for t in texts))


def ranked(candidates: list[Candidate]) -> list[Candidate]:
    """Highest score first; unscored candidates last; ties broken by name then id."""
    return sorted(
        candidates,
        key=lambda c: (c.score is None, -(c.score or 0.0), c.name.lower(), c.id),
    )
