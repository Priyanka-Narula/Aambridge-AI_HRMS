from datetime import date
from decimal import Decimal
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

    nationality: Optional[str] = None
    date_of_birth: Optional[date] = None
    languages_known: Optional[str] = None
    phone: Optional[str] = None
    visa_status: Optional[str] = None
    linkedin_url: Optional[str] = None
    current_location: Optional[str] = None
    preferred_location: Optional[str] = None
    total_experience_years: Optional[Decimal] = None
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    current_ctc: Optional[Decimal] = None
    expected_ctc: Optional[Decimal] = None
    notice_period: Optional[str] = None
    resume_url: Optional[str] = None
    candidate_status: str = "active"
    source: Optional[str] = None
    created_by: Optional[str] = None


class CandidateResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    candidate_status: str

    class Config:
        from_attributes = True