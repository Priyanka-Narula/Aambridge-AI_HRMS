import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SubmissionField(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    required: bool = False


class ContactIn(BaseModel):
    id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    designation: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    primary_contact: bool = False


class ContactOut(BaseModel):
    id: uuid.UUID
    name: str
    designation: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    primary_contact: bool


class ClientCreateRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    company_size: str | None = None
    billing_address: str | None = None
    gst_number: str | None = None
    payment_terms: str | None = None
    portal_url: str | None = None
    submission_format: list[SubmissionField] | None = None
    contacts: list[ContactIn] = []


class ClientUpdateRequest(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    company_size: str | None = None
    billing_address: str | None = None
    gst_number: str | None = None
    payment_terms: str | None = None
    portal_url: str | None = None
    submission_format: list[SubmissionField] | None = None
    contacts: list[ContactIn] | None = None


class ClientStatusUpdate(BaseModel):
    status: Literal["active", "inactive"]


class ClientListItem(BaseModel):
    id: uuid.UUID
    company_name: str
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    company_size: str | None = None
    billing_address: str | None = None
    gst_number: str | None = None
    payment_terms: str | None = None
    portal_url: str | None = None
    status: str
    submission_format: list[SubmissionField] | None = None
    contacts: list[ContactOut] = []
    created_at: datetime | None = None
