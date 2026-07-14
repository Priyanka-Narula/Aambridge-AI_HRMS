from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr, Field


class SkillInput(BaseModel):
    name: str
    years_experience: Optional[Decimal] = None
    proficiency_level: Optional[str] = None


class EducationInput(BaseModel):
    degree: str
    specialization: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    percentage: Optional[Decimal] = None


class WorkExperienceInput(BaseModel):
    company_name: str
    designation: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currently_working: bool = False
    job_description: Optional[str] = None


class CandidateBase(BaseModel):
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
    uae_experience_years: Optional[Decimal] = None
    industry: Optional[str] = None


class CandidateCreate(CandidateBase):
    skills: list[SkillInput] = Field(default_factory=list)
    education_records: list[EducationInput] = Field(default_factory=list)
    work_experiences: list[WorkExperienceInput] = Field(default_factory=list)


class CandidateUpdate(CandidateBase):
    skills: list[SkillInput] = Field(default_factory=list)
    education_records: list[EducationInput] = Field(default_factory=list)
    work_experiences: list[WorkExperienceInput] = Field(default_factory=list)


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    years_experience: Optional[Decimal] = None
    proficiency_level: Optional[str] = None

    model_config = {"from_attributes": True}


class EducationResponse(BaseModel):
    id: uuid.UUID
    degree: str
    specialization: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    percentage: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class WorkExperienceResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    designation: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currently_working: bool
    job_description: Optional[str] = None

    model_config = {"from_attributes": True}


class CandidateResponse(CandidateBase):
    id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    skills: list[SkillResponse] = Field(default_factory=list)
    education_records: list[EducationResponse] = Field(default_factory=list)
    work_experiences: list[WorkExperienceResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
