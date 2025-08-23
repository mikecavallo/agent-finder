from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="sent") # e.g., "sent", "opened", ""failed"

    candidate = relationship("Candidate")
