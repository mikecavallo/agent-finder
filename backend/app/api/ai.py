from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.candidate import Candidate
from app.ai.resume_analyzer import ResumeAnalyzer
from app.config import settings

router = APIRouter()

@router.post("/analyze-resume/{candidate_id}")
async def analyze_single_resume(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not candidate.resume_path:
        raise HTTPException(status_code=400, detail="Candidate has no resume to analyze")

    analyzer = ResumeAnalyzer(api_key=settings.openai_api_key)
    analysis_result = await analyzer.analyze_resume(resume_path=candidate.resume_path)

    candidate.ai_score = analysis_result.get("score")
    candidate.ai_analysis = analysis_result.get("analysis")
    candidate.ai_analyzed_at = datetime.utcnow()
    db.commit()
    db.refresh(candidate)

    return {"message": "Resume analysis complete", "candidate": candidate}

@router.post("/batch-analyze-resumes")
async def batch_analyze_resumes(candidate_ids: List[int], db: Session = Depends(get_db)):
    candidates_to_analyze = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    if not candidates_to_analyze:
        raise HTTPException(status_code=404, detail="No candidates found for analysis")

    analyzer = ResumeAnalyzer(api_key=settings.openai_api_key)
    
    # Filter out candidates without a resume or already analyzed
    filtered_candidates = []
    for cand in candidates_to_analyze:
        if cand.resume_path and not cand.ai_score:
            filtered_candidates.append({"id": cand.id, "resume_path": cand.resume_path})

    if not filtered_candidates:
        return {"message": "No new resumes to analyze among the selected candidates."}

    analysis_results = await analyzer.batch_analyze_resumes(filtered_candidates)

    updated_candidates = []
    for cand in candidates_to_analyze:
        if cand.id in analysis_results:
            result = analysis_results[cand.id]
            cand.ai_score = result.get("score")
            cand.ai_analysis = result.get("analysis")
            cand.ai_analyzed_at = datetime.utcnow()
            db.add(cand)
            updated_candidates.append(cand)
    
    db.commit()
    for cand in updated_candidates:
        db.refresh(cand)

    return {"message": f"Batch analysis complete for {len(updated_candidates)} candidates", "updated_candidates": updated_candidates}
