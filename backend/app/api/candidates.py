from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..ai.providers import ProviderError, get_provider
from ..auth import get_current_user
from ..config import get_settings
from ..database import get_db
from ..models import Candidate, User
from ..schemas import (
    CandidateOut,
    CandidateSummary,
    CandidateUpdate,
    OutreachRequest,
    PastedResume,
    Status,
    UploadError,
    UploadResult,
)
from ..screening import apply_result, job_context, ranked, screen_many
from ..utils.parsing import ParseError, extract_text
from ..utils.validators import validate_filename, validate_resume_text, validate_size
from .jobs import get_owned_job

router = APIRouter()


def get_owned_candidate(candidate_id: int, user: User, db: Session) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None or candidate.job.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")
    return candidate


def _with_rank(candidates: list[Candidate]) -> list[CandidateSummary]:
    out = []
    for i, c in enumerate(candidates, start=1):
        item = CandidateSummary.model_validate(c)
        item.rank = i if c.score is not None else None
        out.append(item)
    return out


async def _screen_and_store(job, items: list[tuple[str, str]], db: Session) -> UploadResult:
    """items: (label, resume_text). Screens all, stores successes, reports failures."""
    settings = get_settings()
    ctx = job_context(job)
    results = await screen_many(
        get_provider(settings), [text for _, text in items], ctx, settings.llm_concurrency
    )
    created, errors = [], []
    for (label, text), result in zip(items, results, strict=True):
        if isinstance(result, ProviderError):
            errors.append(UploadError(filename=label, detail=str(result)))
            continue
        candidate = Candidate(job_id=job.id, resume_text=text, source_filename=label)
        apply_result(candidate, result, ctx)
        db.add(candidate)
        created.append(candidate)
    db.commit()
    return UploadResult(created=[CandidateSummary.model_validate(c) for c in created], errors=errors)


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateSummary])
def list_candidates(
    job_id: int,
    status_filter: Status | None = Query(default=None, alias="status"),
    min_score: float | None = Query(default=None, ge=0, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidates for a job, ranked by score (rank is computed before filtering)."""
    job = get_owned_job(job_id, user, db)
    items = _with_rank(ranked(list(job.candidates)))
    if status_filter:
        items = [c for c in items if c.status == status_filter]
    if min_score is not None:
        items = [c for c in items if c.score is not None and c.score >= min_score]
    return items


@router.post(
    "/jobs/{job_id}/candidates/upload", response_model=UploadResult, status_code=status.HTTP_201_CREATED
)
async def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    job = get_owned_job(job_id, user, db)
    if len(files) > settings.max_files_per_upload:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Upload at most {settings.max_files_per_upload} files at a time."
        )

    items: list[tuple[str, str]] = []
    errors: list[UploadError] = []
    for upload in files:
        name = upload.filename or "unnamed"
        try:
            ext = validate_filename(upload.filename)
            data = await upload.read(settings.max_upload_mb * 1024 * 1024 + 1)
            validate_size(name, len(data), settings.max_upload_mb)
            text = validate_resume_text(extract_text(data, ext), name)
            items.append((name, text))
        except HTTPException as exc:
            errors.append(UploadError(filename=name, detail=str(exc.detail)))
        except ParseError as exc:
            errors.append(UploadError(filename=name, detail=f"{name}: {exc}"))

    result = await _screen_and_store(job, items, db) if items else UploadResult(created=[], errors=[])
    result.errors = errors + result.errors
    if not result.created and result.errors:
        raise HTTPException(422, [e.model_dump() for e in result.errors])
    return result


@router.post(
    "/jobs/{job_id}/candidates/text", response_model=CandidateSummary, status_code=status.HTTP_201_CREATED
)
async def paste_resume(
    job_id: int,
    payload: PastedResume,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = get_owned_job(job_id, user, db)
    text = validate_resume_text(payload.text)
    result = await _screen_and_store(job, [(payload.label or "Pasted text", text)], db)
    if result.errors:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, result.errors[0].detail)
    return result.created[0]


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    candidate = get_owned_candidate(candidate_id, user, db)
    out = CandidateOut.model_validate(candidate)
    ordered = ranked(list(candidate.job.candidates))
    out.rank = (
        next((i for i, c in enumerate(ordered, 1) if c.id == candidate.id), None)
        if candidate.score is not None
        else None
    )
    return out


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def update_candidate(
    candidate_id: int,
    payload: CandidateUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = get_owned_candidate(candidate_id, user, db)
    if payload.status is not None:
        candidate.status = payload.status
    if payload.notes is not None:
        candidate.notes = payload.notes
    db.commit()
    db.refresh(candidate)
    return CandidateOut.model_validate(candidate)


@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    db.delete(get_owned_candidate(candidate_id, user, db))
    db.commit()


@router.post("/candidates/{candidate_id}/rescore", response_model=CandidateOut)
async def rescore_candidate(
    candidate_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Re-run screening, e.g. after the job's criteria changed or a different provider is configured."""
    candidate = get_owned_candidate(candidate_id, user, db)
    ctx = job_context(candidate.job)
    try:
        result = await get_provider(get_settings()).screen(candidate.resume_text, ctx)
    except ProviderError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    apply_result(candidate, result, ctx)
    db.commit()
    db.refresh(candidate)
    return CandidateOut.model_validate(candidate)


@router.post("/candidates/{candidate_id}/outreach", response_model=CandidateOut)
async def draft_outreach(
    candidate_id: int,
    payload: OutreachRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an outreach email draft. Nothing is sent; the recruiter copies and edits it."""
    from ..ai.extraction import ExtractedProfile

    candidate = get_owned_candidate(candidate_id, user, db)
    profile = ExtractedProfile(name=candidate.name, summary=candidate.summary)
    highlights = list(candidate.strengths or [])
    try:
        draft = await get_provider(get_settings()).draft_outreach(
            profile, highlights, job_context(candidate.job), payload.recruiter_name
        )
    except ProviderError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    candidate.outreach_draft = draft
    db.commit()
    db.refresh(candidate)
    return CandidateOut.model_validate(candidate)
