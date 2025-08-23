# models/candidate.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    state = Column(String(50), nullable=False)
    city = Column(String(100), nullable=True)
    
    # Profile Information
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    experience_years = Column(Integer, nullable=True)
    education = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    
    # Source Information
    source = Column(String(50), nullable=False)  # 'indeed' or 'linkedin'
    profile_url = Column(String(500), nullable=True)
    resume_path = Column(String(500), nullable=True)
    
    # AI Analysis
    ai_score = Column(Float, nullable=True)
    ai_analysis = Column(Text, nullable=True)
    ai_analyzed_at = Column(DateTime, nullable=True)
    
    # Communication Tracking
    contacted = Column(Boolean, default=False)
    contacted_date = Column(DateTime, nullable=True)
    email_sent = Column(Boolean, default=False)
    email_sent_date = Column(DateTime, nullable=True)
    
    # Metadata
    date_added = Column(DateTime, nullable=False)
    last_updated = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
