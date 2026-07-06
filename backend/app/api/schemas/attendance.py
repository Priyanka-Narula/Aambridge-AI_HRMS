import uuid
from datetime import date, datetime

from pydantic import BaseModel


class AttendanceRecordResponse(BaseModel):
    date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: str  # "on_time" | "late" | "absent"


class AttendancePolicyResponse(BaseModel):
    checkin_expected: str
    checkout_expected: str
    late_threshold: str
    timezone: str


class RecruiterAttendanceRow(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str
    employee_code: str | None = None
    designation: str | None = None
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: str  # "on_time" | "late" | "absent"
