import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RecruiterCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    personal_email: EmailStr | None = None
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = None
    location: str | None = None
    languages_spoken: str | None = None
    employee_code: str = Field(min_length=1, max_length=50)
    designation: str | None = None
    team: str | None = None
    joining_date: date | None = None


class RecruiterUpdateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    personal_email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    languages_spoken: str | None = None
    employee_code: str = Field(min_length=1, max_length=50)
    designation: str | None = None
    team: str | None = None
    joining_date: date | None = None


class UserStatusUpdate(BaseModel):
    status: Literal["active", "inactive"]


class RecruiterPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class RecruiterSummary(BaseModel):
    id: uuid.UUID
    employee_code: str
    designation: str | None = None
    team: str | None = None
    joining_date: date | None = None
    status: str


class UserListItem(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    personal_email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    languages_spoken: str | None = None
    status: str
    role: str
    recruiter: RecruiterSummary | None = None
    created_at: datetime | None = None
