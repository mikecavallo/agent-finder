from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.candidate import Candidate
from app.models.email_campaign import EmailCampaign
from app.email.sender import send_email
from app.email.templates import get_initial_outreach_template

router = APIRouter()

@router.post("/send/{candidate_id}")
async def send_email_to_candidate(candidate_id: int, recruiter_name: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not candidate.email:
        raise HTTPException(status_code=400, detail="Candidate has no email address")

    template = get_initial_outreach_template(candidate.name, recruiter_name)
    subject = template["subject"]
    body = template["body"]

    email_sent = await send_email(candidate.email, subject, body)

    if email_sent:
        candidate.contacted = True
        candidate.contacted_date = datetime.utcnow()
        candidate.email_sent = True
        candidate.email_sent_date = datetime.utcnow()
        
        email_campaign = EmailCampaign(
            candidate_id=candidate.id,
            subject=subject,
            body=body,
            sent_at=datetime.utcnow(),
            status="sent"
        )
        db.add(email_campaign)
        db.commit()
        db.refresh(candidate)
        db.refresh(email_campaign)
        return {"message": f"Email sent to {candidate.name}", "candidate": candidate}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email")

@router.post("/bulk-send")
async def bulk_send_emails(candidate_ids: List[int], recruiter_name: str, db: Session = Depends(get_db)):
    successful_sends = []
    failed_sends = []

    for candidate_id in candidate_ids:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            failed_sends.append({"id": candidate_id, "reason": "Candidate not found"})
            continue
        if not candidate.email:
            failed_sends.append({"id": candidate_id, "reason": "Candidate has no email address"})
            continue

        template = get_initial_outreach_template(candidate.name, recruiter_name)
        subject = template["subject"]
        body = template["body"]

        email_sent = await send_email(candidate.email, subject, body)

        if email_sent:
            candidate.contacted = True
            candidate.contacted_date = datetime.utcnow()
            candidate.email_sent = True
            candidate.email_sent_date = datetime.utcnow()
            
            email_campaign = EmailCampaign(
                candidate_id=candidate.id,
                subject=subject,
                body=body,
                sent_at=datetime.utcnow(),
                status="sent"
            )
            db.add(email_campaign)
            db.commit()
            db.refresh(candidate)
            db.refresh(email_campaign)
            successful_sends.append({"id": candidate.id, "name": candidate.name})
        else:
            failed_sends.append({"id": candidate.id, "reason": "Failed to send email"})
    
    return {
        "message": f"Bulk email operation complete. Sent to {len(successful_sends)} candidates, failed for {len(failed_sends)}.",
        "successful_sends": successful_sends,
        "failed_sends": failed_sends
    }

@router.get("/campaigns")
async def get_email_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(EmailCampaign).all()
    return campaigns
