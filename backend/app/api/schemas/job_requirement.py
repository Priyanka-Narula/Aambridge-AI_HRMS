import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobRequirementCreateRequest(BaseModel):
    client_id: uuid.UUID
    assigned_to: uuid.UUID
    job_title: str = Field(min_length=1, max_length=255)
    department: str | None = None
    employment_type: str | None = None
    work_mode: str | None = None
    experience_min: Decimal | None = None
    experience_max: Decimal | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    open_positions: int | None = Field(default=None, ge=1)
    job_description: str | None = None
    location: str | None = None
    priority: str | None = None
    requirement_type: str | None = None
    status: Literal["open", "on_hold", "closed", "filled"] = "open"


class JobRequirementUpdateRequest(BaseModel):
    client_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    job_title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = None
    employment_type: str | None = None
    work_mode: str | None = None
    experience_min: Decimal | None = None
    experience_max: Decimal | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    open_positions: int | None = Field(default=None, ge=1)
    job_description: str | None = None
    location: str | None = None
    priority: str | None = None
    requirement_type: str | None = None
    status: Literal["open", "on_hold", "closed", "filled"] | None = None


class JobRequirementStatusUpdate(BaseModel):
    status: Literal["open", "on_hold", "closed", "filled"]


class JobRequirementListItem(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    assigned_to: uuid.UUID | None = None
    assigned_recruiter_name: str | None = None
    job_title: str
    department: str | None = None
    employment_type: str | None = None
    work_mode: str | None = None
    experience_min: Decimal | None = None
    experience_max: Decimal | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    open_positions: int | None = None
    job_description: str | None = None
    location: str | None = None
    priority: str | None = None
    status: str
    requirement_type: str | None = None
    created_by: uuid.UUID
    created_at: datetime | None = None
    client_submission_format: list[dict[str, Any]] | None = None
    submitted_candidates: int = 0
    pipeline_candidates: int = 0
    joined_candidates: int = 0
    remaining_positions: int | None = None
    submissions_enabled: bool = True
