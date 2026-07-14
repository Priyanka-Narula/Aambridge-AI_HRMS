from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class SkillDraft(BaseModel):
    name: str
    years_experience: Decimal | None = None
    proficiency_level: str | None = None


class EducationDraft(BaseModel):
    degree: str
    specialization: str | None = None
    institution: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    percentage: Decimal | None = None


class WorkExperienceDraft(BaseModel):
    company_name: str
    designation: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    currently_working: bool = False
    job_description: str | None = None


class CandidateDraft(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    nationality: str | None = None
    date_of_birth: date | None = None
    languages_known: str | None = None
    phone: str | None = None
    visa_status: str | None = None
    linkedin_url: str | None = None
    current_location: str | None = None
    preferred_location: str | None = None
    total_experience_years: Decimal | None = None
    uae_experience_years: Decimal | None = None
    industry: str | None = None
    current_company: str | None = None
    current_designation: str | None = None
    current_ctc: Decimal | None = None
    expected_ctc: Decimal | None = None
    notice_period: str | None = None
    resume_url: str
    source: str | None = None
    candidate_status: str = "active"
    skills: list[SkillDraft] = Field(default_factory=list)
    education: list[EducationDraft] = Field(default_factory=list)
    work_experience: list[WorkExperienceDraft] = Field(default_factory=list)


class CandidateApprovalRequest(BaseModel):
    candidate: CandidateDraft
    created_by: str | None = None


class DriveSyncRequest(BaseModel):
    folder_path: str | None = None
    max_files: int = 25
    auto_approve: bool = False
    created_by: str | None = "drive-sync-ingestor"
