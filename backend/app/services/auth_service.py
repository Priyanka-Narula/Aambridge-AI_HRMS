from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import (
    ALLOWED_ROLES,
    ROLE_OWNER,
    create_access_token,
    hash_password,
    normalize_role,
    verify_password,
)
from app.models.user_access import Role, User


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.recruiter))
        .filter(User.email == email.lower())
        .first()
    )
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    role_name = normalize_role(user.role.name)
    if role_name not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted to log in")
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(str(user.id), user.role.name)


def serialize_user(user: User) -> dict:
    recruiter = None
    if user.recruiter:
        recruiter = {
            "id": user.recruiter.id,
            "employee_code": user.recruiter.employee_code,
            "designation": user.recruiter.designation,
            "team": user.recruiter.team,
            "status": user.recruiter.status,
        }
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "location": user.location,
        "languages_spoken": user.languages_spoken,
        "status": user.status,
        "role": normalize_role(user.role.name),
        "recruiter": recruiter,
        "created_at": user.created_at,
    }


def ensure_bootstrap_owner(db: Session) -> None:
    owner_role = db.query(Role).filter(Role.name == ROLE_OWNER).first()
    if not owner_role:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            admin_role.name = ROLE_OWNER
            owner_role = admin_role
        else:
            owner_role = Role(name=ROLE_OWNER)
            db.add(owner_role)
        db.flush()

    existing_owner = (
        db.query(User).join(Role).filter(Role.name == ROLE_OWNER).first()
    )
    if existing_owner or not settings.BOOTSTRAP_OWNER_PASSWORD:
        db.commit()
        return

    owner = User(
        first_name=settings.BOOTSTRAP_OWNER_FIRST_NAME,
        last_name=settings.BOOTSTRAP_OWNER_LAST_NAME,
        email=settings.BOOTSTRAP_OWNER_EMAIL.lower(),
        password_hash=hash_password(settings.BOOTSTRAP_OWNER_PASSWORD),
        role_id=owner_role.id,
        status="active",
    )
    db.add(owner)
    db.commit()
