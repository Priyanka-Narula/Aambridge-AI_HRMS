import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.user import RecruiterCreateRequest, RecruiterUpdateRequest, UserStatusUpdate
from app.core.security import ROLE_RECRUITER, hash_password, normalize_role
from app.models.user_access import Recruiter, Role, User


def _user_query(db: Session):
    return db.query(User).options(joinedload(User.role), joinedload(User.recruiter))


def list_users(db: Session) -> list[User]:
    return (
        _user_query(db)
        .join(Role)
        .filter(Role.name.in_([ROLE_RECRUITER, "recruiter"]))
        .order_by(User.created_at.desc())
        .all()
    )


def serialize_user_list_item(user: User) -> dict:
    recruiter = None
    if user.recruiter:
        recruiter = {
            "id": user.recruiter.id,
            "employee_code": user.recruiter.employee_code,
            "designation": user.recruiter.designation,
            "team": user.recruiter.team,
            "joining_date": user.recruiter.joining_date,
            "status": user.recruiter.status,
        }
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "personal_email": user.personal_email,
        "phone": user.phone,
        "location": user.location,
        "languages_spoken": user.languages_spoken,
        "status": user.status,
        "role": normalize_role(user.role.name),
        "recruiter": recruiter,
        "created_at": user.created_at,
    }


def create_recruiter(db: Session, payload: RecruiterCreateRequest) -> User:
    recruiter_role = db.query(Role).filter(Role.name == ROLE_RECRUITER).first()
    if not recruiter_role:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Recruiter role not configured")

    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if db.query(Recruiter).filter(Recruiter.employee_code == payload.employee_code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee code already exists")

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        personal_email=str(payload.personal_email).lower() if payload.personal_email else None,
        phone=payload.phone,
        location=payload.location,
        languages_spoken=payload.languages_spoken,
        password_hash=hash_password(payload.password),
        role_id=recruiter_role.id,
        status="active",
    )
    db.add(user)
    db.flush()

    recruiter = Recruiter(
        user_id=user.id,
        employee_code=payload.employee_code,
        designation=payload.designation,
        team=payload.team,
        joining_date=payload.joining_date,
        status="active",
    )
    db.add(recruiter)
    db.commit()
    return _user_query(db).filter(User.id == user.id).one()


def get_user_or_404(db: Session, user_id: uuid.UUID) -> User:
    user = _user_query(db).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if normalize_role(user.role.name) != ROLE_RECRUITER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only recruiter accounts can be managed here")
    return user


def update_recruiter(db: Session, user_id: uuid.UUID, payload: RecruiterUpdateRequest) -> User:
    user = get_user_or_404(db, user_id)
    if not user.recruiter:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recruiter profile not found")

    email = str(payload.email).lower()
    existing_email = db.query(User).filter(User.email == email, User.id != user_id).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    existing_code = (
        db.query(Recruiter)
        .filter(Recruiter.employee_code == payload.employee_code, Recruiter.id != user.recruiter.id)
        .first()
    )
    if existing_code:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee code already exists")

    user.first_name = payload.first_name
    user.last_name = payload.last_name
    user.email = email
    user.personal_email = str(payload.personal_email).lower() if payload.personal_email else None
    user.phone = payload.phone
    user.location = payload.location
    user.languages_spoken = payload.languages_spoken

    user.recruiter.employee_code = payload.employee_code
    user.recruiter.designation = payload.designation
    user.recruiter.team = payload.team
    user.recruiter.joining_date = payload.joining_date

    db.commit()
    return _user_query(db).filter(User.id == user_id).one()


def update_user_status(db: Session, user_id: uuid.UUID, payload: UserStatusUpdate) -> User:
    user = get_user_or_404(db, user_id)
    if user.recruiter:
        user.recruiter.status = payload.status
    db.commit()
    return _user_query(db).filter(User.id == user_id).one()
