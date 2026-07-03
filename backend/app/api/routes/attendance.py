from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.attendance import AttendanceRecordResponse, RecruiterAttendanceRow
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_owner
from app.models.attendance import AttendanceRecord
from app.models.user_access import Role, User

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])

_LATE_THRESHOLD = time(*[int(p) for p in settings.LATE_THRESHOLD.split(":")])


def _office_tz() -> ZoneInfo:
    return ZoneInfo(settings.OFFICE_TIMEZONE)


def _today_office() -> "date":  # noqa: F821
    from datetime import date as _date  # local import to keep module-level clean
    return datetime.now(_office_tz()).date()


def _compute_status(check_in_utc: datetime | None) -> str:
    if check_in_utc is None:
        return "absent"
    local_time = check_in_utc.astimezone(_office_tz()).time()
    return "on_time" if local_time <= _LATE_THRESHOLD else "late"


def _get_or_create_record(db: Session, user_id, today) -> AttendanceRecord:
    record = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.user_id == user_id, AttendanceRecord.date == today)
        .first()
    )
    if not record:
        record = AttendanceRecord(user_id=user_id, date=today)
        db.add(record)
        db.flush()
    return record


def _serialize(record: AttendanceRecord | None, today) -> AttendanceRecordResponse:
    if record is None:
        return AttendanceRecordResponse(date=today, status="absent")
    return AttendanceRecordResponse(
        date=record.date,
        check_in=record.check_in,
        check_out=record.check_out,
        status=_compute_status(record.check_in),
    )


# ── Recruiter: check in ──────────────────────────────────────────────────────

@router.post("/checkin", response_model=AttendanceRecordResponse)
def check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = _today_office()
    record = _get_or_create_record(db, current_user.id, today)
    if record.check_in is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already checked in today",
        )
    record.check_in = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return _serialize(record, today)


# ── Recruiter: check out ─────────────────────────────────────────────────────

@router.post("/checkout", response_model=AttendanceRecordResponse)
def check_out(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = _today_office()
    record = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.user_id == current_user.id, AttendanceRecord.date == today)
        .first()
    )
    if record is None or record.check_in is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must check in before checking out",
        )
    if record.check_out is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already checked out today",
        )
    record.check_out = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return _serialize(record, today)


# ── Any user: my today record ────────────────────────────────────────────────

@router.get("/today/me", response_model=AttendanceRecordResponse)
def my_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = _today_office()
    record = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.user_id == current_user.id, AttendanceRecord.date == today)
        .first()
    )
    return _serialize(record, today)


# ── Owner: all recruiters today ──────────────────────────────────────────────

@router.get("/today", response_model=list[RecruiterAttendanceRow])
def all_today(
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    today = _today_office()

    recruiter_role = db.query(Role).filter(Role.name == "recruiter").first()
    if not recruiter_role:
        return []

    users = (
        db.query(User)
        .options(joinedload(User.recruiter))
        .filter(User.role_id == recruiter_role.id, User.status == "active")
        .order_by(User.first_name)
        .all()
    )
    if not users:
        return []

    user_ids = [u.id for u in users]
    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.user_id.in_(user_ids), AttendanceRecord.date == today)
        .all()
    )
    records_map = {r.user_id: r for r in records}

    rows: list[RecruiterAttendanceRow] = []
    for u in users:
        rec = records_map.get(u.id)
        rows.append(
            RecruiterAttendanceRow(
                user_id=u.id,
                first_name=u.first_name,
                last_name=u.last_name,
                employee_code=u.recruiter.employee_code if u.recruiter else None,
                designation=u.recruiter.designation if u.recruiter else None,
                check_in=rec.check_in if rec else None,
                check_out=rec.check_out if rec else None,
                status=_compute_status(rec.check_in if rec else None),
            )
        )
    return rows
