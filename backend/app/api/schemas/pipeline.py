from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class PipelineStageResponse(BaseModel):
    id: uuid.UUID
    name: str
    order_no: int


class InterviewRoundResponse(BaseModel):
    id: uuid.UUID
    interview_round: int
    status: str
    scheduled_datetime: datetime | None = None
    mode: str | None = None
    interviewer_name: str | None = None


class PipelineCardResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    candidate_phone: str | None = None
    current_designation: str | None = None
    current_company: str | None = None
    total_experience_years: float | None = None
    job_requirement_id: uuid.UUID
    job_title: str
    client_id: uuid.UUID
    client_name: str
    assigned_recruiter_id: uuid.UUID | None = None
    assigned_recruiter_name: str | None = None
    job_assignee_user_id: uuid.UUID | None = None
    job_assignee_name: str | None = None
    current_stage_id: uuid.UUID | None = None
    current_stage: str | None = None
    status: str
    owner_status: str
    in_pipeline: bool = False
    applied_date: date | None = None
    submitted_at: datetime | None = None
    remarks: str | None = None
    interview_round: int | None = None
    interview_scheduled_at: datetime | None = None
    interview_mode: str | None = None
    interview_status: str | None = None
    interviewer_name: str | None = None
    interviews: list[InterviewRoundResponse] = []
    offer_ctc: Decimal | None = None
    offer_date: date | None = None
    offer_status: str | None = None
    offer_joining_date: date | None = None
    joined_date: date | None = None


class PipelineBoardResponse(BaseModel):
    stages: list[PipelineStageResponse]
    cards: list[PipelineCardResponse]


class StageHistoryItem(BaseModel):
    id: uuid.UUID
    stage_id: uuid.UUID
    stage_name: str
    moved_by: uuid.UUID
    moved_by_name: str | None = None
    remarks: str | None = None
    created_at: datetime


class CandidateApplicationHistory(BaseModel):
    application_id: uuid.UUID
    job_requirement_id: uuid.UUID
    job_title: str
    client_id: uuid.UUID
    client_name: str
    current_stage: str | None = None
    owner_status: str
    status: str
    submitted_at: datetime | None = None
    history: list[StageHistoryItem]


class CandidateStageHistoryResponse(BaseModel):
    candidate_id: uuid.UUID
    applications: list[CandidateApplicationHistory]


class PipelineMoveRequest(BaseModel):
    stage_name: str
    remarks: str | None = None
    offered_ctc: Decimal | None = None
    joining_date: date | None = None
    joined_date: date | None = None
    revenue_generated: Decimal | None = None
    interview_scheduled_at: datetime | None = None
    interviewer_name: str | None = None
    interview_mode: str | None = None


class InterviewActionRequest(BaseModel):
    action: Literal["cancel", "change_date", "no_show", "reschedule"]
    interview_scheduled_at: datetime | None = None
    interviewer_name: str | None = None
    interview_mode: str | None = None
    remarks: str | None = None


class ShortlistRequest(BaseModel):
    application_ids: list[uuid.UUID] = Field(min_length=1)
    remarks: str | None = "Shortlisted by client"


class ShareApprovedRequest(BaseModel):
    to_emails: list[str] | None = None
    subject: str | None = None
    message: str | None = None
    application_ids: list[uuid.UUID] | None = None


class ShareApprovedResponse(BaseModel):
    sent_to: list[str]
    subject: str
    attachment: str | None = None
    candidate_count: int


class EmailStatusResponse(BaseModel):
    configured: bool
