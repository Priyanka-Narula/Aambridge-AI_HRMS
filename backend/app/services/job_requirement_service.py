import uuid

from fastapi import HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.job_requirement import (
    JobRequirementCreateRequest,
    JobRequirementStatusUpdate,
    JobRequirementUpdateRequest,
)
from app.core.security import ROLE_OWNER, ROLE_RECRUITER, normalize_role
from app.models.job_requirement import JobRequirement
from app.models.offer import Placement
from app.models.pipeline import CandidateApplication
from app.models.user_access import Client, User


def get_job_pipeline_metrics(
    db: Session,
    requirement_ids: list[uuid.UUID] | set[uuid.UUID],
) -> dict[uuid.UUID, dict[str, int]]:
    """Return submission, pipeline, and joined counts without join multiplication."""
    ids = list(requirement_ids)
    if not ids:
        return {}

    metrics: dict[uuid.UUID, dict[str, int]] = {
        requirement_id: {
            "submitted_candidates": 0,
            "pipeline_candidates": 0,
            "joined_candidates": 0,
        }
        for requirement_id in ids
    }

    application_rows = (
        db.query(
            CandidateApplication.job_requirement_id,
            func.count(CandidateApplication.id),
            func.sum(
                case(
                    (
                        CandidateApplication.in_pipeline.is_(True),
                        1,
                    ),
                    else_=0,
                )
            ),
        )
        .filter(CandidateApplication.job_requirement_id.in_(ids))
        .group_by(CandidateApplication.job_requirement_id)
        .all()
    )
    for requirement_id, submitted_count, pipeline_count in application_rows:
        metrics[requirement_id]["submitted_candidates"] = int(submitted_count or 0)
        metrics[requirement_id]["pipeline_candidates"] = int(pipeline_count or 0)

    joined_rows = (
        db.query(
            CandidateApplication.job_requirement_id,
            func.count(Placement.id),
        )
        .join(Placement, Placement.application_id == CandidateApplication.id)
        .filter(
            CandidateApplication.job_requirement_id.in_(ids),
            Placement.joined_date.is_not(None),
        )
        .group_by(CandidateApplication.job_requirement_id)
        .all()
    )
    for requirement_id, joined_count in joined_rows:
        metrics[requirement_id]["joined_candidates"] = int(joined_count or 0)

    return metrics


def get_job_pipeline_metric(db: Session, requirement_id: uuid.UUID) -> dict[str, int]:
    return get_job_pipeline_metrics(db, [requirement_id])[requirement_id]


def is_job_fulfilled(
    requirement: JobRequirement,
    joined_candidates: int,
) -> bool:
    return bool(
        requirement.open_positions is not None
        and requirement.open_positions > 0
        and joined_candidates >= requirement.open_positions
    )


def close_job_if_fulfilled(db: Session, requirement: JobRequirement) -> bool:
    """Close a job once its joined count reaches its required positions."""
    joined_candidates = get_job_pipeline_metric(db, requirement.id)["joined_candidates"]
    if is_job_fulfilled(requirement, joined_candidates):
        requirement.status = "closed"
        return True
    return False


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

    db.flush()
    close_job_if_fulfilled(db, requirement)
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
    if payload.status == "open":
        joined_candidates = get_job_pipeline_metric(db, requirement.id)["joined_candidates"]
        if is_job_fulfilled(requirement, joined_candidates):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "This job cannot be reopened because all positions are filled. "
                    "Increase the number of open positions first."
                ),
            )
    requirement.status = payload.status
    db.commit()
    return _query(db).filter(JobRequirement.id == requirement.id).one()


def serialize_job_requirement(
    requirement: JobRequirement,
    pipeline_metrics: dict[str, int] | None = None,
) -> dict:
    import json

    assignee = requirement.assignee
    assignee_name = None
    if assignee:
        assignee_name = f"{assignee.first_name} {assignee.last_name}".strip()

    client_submission_format = None
    if requirement.client and requirement.client.submission_format:
        try:
            client_submission_format = json.loads(requirement.client.submission_format)
        except (json.JSONDecodeError, TypeError):
            client_submission_format = None

    metrics = pipeline_metrics or {
        "submitted_candidates": 0,
        "pipeline_candidates": 0,
        "joined_candidates": 0,
    }
    joined_candidates = metrics["joined_candidates"]
    remaining_positions = (
        max(requirement.open_positions - joined_candidates, 0)
        if requirement.open_positions is not None
        else None
    )
    submissions_enabled = requirement.status == "open" and not is_job_fulfilled(
        requirement,
        joined_candidates,
    )

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
        "client_submission_format": client_submission_format,
        "submitted_candidates": metrics["submitted_candidates"],
        "pipeline_candidates": metrics["pipeline_candidates"],
        "joined_candidates": joined_candidates,
        "remaining_positions": remaining_positions,
        "submissions_enabled": submissions_enabled,
    }
