import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RecruiterProfile(BaseModel):
    id: uuid.UUID
    employee_code: str
    designation: str | None = None
    team: str | None = None
    status: str

    model_config = {"from_attributes": True}


class UserMeResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    languages_spoken: str | None = None
    status: str
    role: str
    recruiter: RecruiterProfile | None = None
    created_at: datetime | None = None
