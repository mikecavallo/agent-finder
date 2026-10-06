"""Demo-mode seeding: a demo account, one sample opening, and fictional resumes."""

import asyncio
import logging
from pathlib import Path

from sqlalchemy import select

from ..ai.providers import ProviderError, get_provider
from ..ai.rubric import JobCriteria
from ..auth import hash_password
from ..config import Settings
from ..database import SessionLocal
from ..models import Candidate, Job, User
from ..screening import apply_result, job_context

logger = logging.getLogger(__name__)
RESUME_DIR = Path(__file__).parent / "resumes"

DEMO_JOB = {
    "title": "Licensed Insurance Agent (Personal Lines)",
    "location": "Wilmington, NC",
    "description": (
        "Fictional demo opening. Agency sells home, auto and life coverage to local families. "
        "Agent handles inbound leads, quotes and binds policies, and services existing clients."
    ),
    "criteria": JobCriteria(
        required_licenses=["P&C", "Life & Health"],
        min_sales_years=2,
        customer_service_required=True,
        bilingual_preferred=True,
        languages=["Spanish"],
    ).model_dump(),
}


def sample_resumes() -> list[tuple[str, str]]:
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(RESUME_DIR.glob("*.txt"))]


async def seed_demo(settings: Settings) -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == settings.demo_username))
        if user is None:
            user = User(
                username=settings.demo_username,
                email=f"{settings.demo_username}@example.com",
                hashed_password=hash_password(settings.demo_password),
            )
            db.add(user)
            db.commit()
            logger.info("Demo mode: created user '%s'", settings.demo_username)
        if db.scalar(select(Job).where(Job.owner_id == user.id)) is not None:
            return

        job = Job(owner_id=user.id, **DEMO_JOB)
        db.add(job)
        db.commit()
        ctx = job_context(job)
        provider = get_provider(settings)
        for filename, text in sample_resumes():
            try:
                result = await provider.screen(text, ctx)
            except ProviderError as exc:
                logger.warning("Demo mode: could not screen %s: %s", filename, exc)
                continue
            candidate = Candidate(job_id=job.id, resume_text=text, source_filename=filename)
            apply_result(candidate, result, ctx)
            db.add(candidate)
        db.commit()
        logger.info("Demo mode: seeded sample opening with %d resumes", len(job.candidates))


def run() -> None:
    """CLI entry point: python -m app.demo.seed"""
    from ..config import get_settings
    from ..database import init_db

    init_db()
    asyncio.run(seed_demo(get_settings()))


if __name__ == "__main__":
    run()
