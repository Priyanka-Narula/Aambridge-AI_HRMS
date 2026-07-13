import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.job_requirement import (
    JobRequirementCreateRequest,
    JobRequirementStatusUpdate,
    JobRequirementUpdateRequest,
)
from app.core.security import ROLE_OWNER, ROLE_RECRUITER, normalize_role
from app.models.job_requirement import JobRequirement
from app.models.user_access import Client, User


def _query(db: Session):
    return db.query(JobRequirement).options(
        joinedload(JobRequirement.client),
        joinedload(JobRequirement.assignee),
    )


def _assert_client_exists(db: Session, client_id: uuid.UUID) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


def _assert_recruiter_user(db: Session, user_id: uuid.UUID) -> User:
    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.recruiter))
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")
    if normalize_role(user.role.name) != ROLE_RECRUITER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assigned user must be a recruiter",
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assigned recruiter is inactive",
        )
    return user


def list_job_requirements(db: Session, current_user: User) -> list[JobRequirement]:
    query = _query(db)
    role = normalize_role(current_user.role.name)
    if role == ROLE_RECRUITER:
        query = query.filter(JobRequirement.assigned_to == current_user.id)
    return query.order_by(JobRequirement.created_at.desc()).all()


def get_job_requirement(
    db: Session,
    requirement_id: uuid.UUID,
    current_user: User,
) -> JobRequirement:
    requirement = _query(db).filter(JobRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requirement not found",
        )

    role = normalize_role(current_user.role.name)
    if role == ROLE_RECRUITER and requirement.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return requirement


def create_job_requirement(
    db: Session,
    payload: JobRequirementCreateRequest,
    current_user: User,
) -> JobRequirement:
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    _assert_client_exists(db, payload.client_id)
    _assert_recruiter_user(db, payload.assigned_to)

    requirement = JobRequirement(
        client_id=payload.client_id,
        assigned_to=payload.assigned_to,
        job_title=payload.job_title.strip(),
        department=payload.department,
        employment_type=payload.employment_type,
        work_mode=payload.work_mode,
        experience_min=payload.experience_min,
        experience_max=payload.experience_max,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        open_positions=payload.open_positions,
        job_description=payload.job_description,
        location=payload.location,
        priority=payload.priority,
        requirement_type=payload.requirement_type,
        status=payload.status,
        created_by=current_user.id,
    )
    db.add(requirement)
    db.commit()
    return _query(db).filter(JobRequirement.id == requirement.id).one()


def update_job_requirement(
    db: Session,
    requirement_id: uuid.UUID,
    payload: JobRequirementUpdateRequest,
    current_user: User,
) -> JobRequirement:
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    requirement = _query(db).filter(JobRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requirement not found",
        )

    data = payload.model_dump(exclude_unset=True)
    if "client_id" in data and data["client_id"] is not None:
        _assert_client_exists(db, data["client_id"])
        requirement.client_id = data["client_id"]
    if "assigned_to" in data and data["assigned_to"] is not None:
        _assert_recruiter_user(db, data["assigned_to"])
        requirement.assigned_to = data["assigned_to"]
    if "job_title" in data and data["job_title"] is not None:
        requirement.job_title = data["job_title"].strip()

    for field in (
        "department",
        "employment_type",
        "work_mode",
        "experience_min",
        "experience_max",
        "salary_min",
        "salary_max",
        "open_positions",
        "job_description",
        "location",
        "priority",
        "requirement_type",
        "status",
    ):
        if field in data:
            setattr(requirement, field, data[field])

    db.commit()
    return _query(db).filter(JobRequirement.id == requirement.id).one()


def update_job_requirement_status(
    db: Session,
    requirement_id: uuid.UUID,
    payload: JobRequirementStatusUpdate,
    current_user: User,
) -> JobRequirement:
    if normalize_role(current_user.role.name) != ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    requirement = get_job_requirement(db, requirement_id, current_user)
    requirement.status = payload.status
    db.commit()
    return _query(db).filter(JobRequirement.id == requirement.id).one()


def serialize_job_requirement(requirement: JobRequirement) -> dict:
    assignee = requirement.assignee
    assignee_name = None
    if assignee:
        assignee_name = f"{assignee.first_name} {assignee.last_name}".strip()

    return {
        "id": requirement.id,
        "client_id": requirement.client_id,
        "client_name": requirement.client.company_name if requirement.client else "",
        "assigned_to": requirement.assigned_to,
        "assigned_recruiter_name": assignee_name,
        "job_title": requirement.job_title,
        "department": requirement.department,
        "employment_type": requirement.employment_type,
        "work_mode": requirement.work_mode,
        "experience_min": requirement.experience_min,
        "experience_max": requirement.experience_max,
        "salary_min": requirement.salary_min,
        "salary_max": requirement.salary_max,
        "open_positions": requirement.open_positions,
        "job_description": requirement.job_description,
        "location": requirement.location,
        "priority": requirement.priority,
        "status": requirement.status,
        "requirement_type": requirement.requirement_type,
        "created_by": requirement.created_by,
        "created_at": requirement.created_at,
    }
