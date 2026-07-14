import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class CandidateSubmitRequest(BaseModel):
    candidate_id: uuid.UUID
    submission_data: dict[str, Any] | None = None


class OwnerApprovalRequest(BaseModel):
    action: Literal["approved", "rejected"]
    remarks: str | None = None


class CandidateSubmissionResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    job_requirement_id: uuid.UUID
    job_title: str
    client_id: uuid.UUID
    client_name: str
    submitted_by_id: uuid.UUID | None
    submitted_by_name: str | None
    submitted_at: datetime | None
    current_stage: str | None
    status: str
    owner_status: str
    submission_data: dict[str, Any] | None = None


class OwnerDashboardJob(BaseModel):
    job_requirement_id: uuid.UUID
    job_title: str
    status: str
    open_positions: int | None
    submissions: list[CandidateSubmissionResponse]


class OwnerDashboardClient(BaseModel):
    client_id: uuid.UUID
    company_name: str
    jobs: list[OwnerDashboardJob]
