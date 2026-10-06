from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Job, User
from ..schemas import JobIn, JobOut, JobUpdate

router = APIRouter()


def get_owned_job(job_id: int, user: User, db: Session) -> Job:
    job = db.get(Job, job_id)
    if job is None or job.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


def to_out(job: Job) -> JobOut:
    out = JobOut.model_validate(job)
    out.candidate_count = len(job.candidates)
    out.shortlisted_count = sum(1 for c in job.candidates if c.status == "shortlisted")
    return out


@router.get("", response_model=list[JobOut])
def list_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).where(Job.owner_id == user.id).order_by(Job.created_at.desc())).all()
    return [to_out(j) for j in jobs]


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = Job(
        owner_id=user.id,
        title=payload.title,
        location=payload.location,
        description=payload.description,
        criteria=payload.criteria.model_dump(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return to_out(job)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return to_out(get_owned_job(job_id, user, db))


@router.patch("/{job_id}", response_model=JobOut)
def update_job(
    job_id: int, payload: JobUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = get_owned_job(job_id, user, db)
    data = payload.model_dump(exclude_unset=True)
    if "criteria" in data and payload.criteria is not None:
        data["criteria"] = payload.criteria.model_dump()
    for key, value in data.items():
        if value is not None:
            setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return to_out(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_owned_job(job_id, user, db))
    db.commit()
