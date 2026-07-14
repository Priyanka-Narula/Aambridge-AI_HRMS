import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.job_requirement import (
    JobRequirementCreateRequest,
    JobRequirementListItem,
    JobRequirementStatusUpdate,
    JobRequirementUpdateRequest,
)
from app.core.database import get_db
from app.core.deps import get_current_user, require_owner
from app.models.user_access import User
from app.services.job_requirement_service import (
    create_job_requirement,
    get_job_requirement,
    list_job_requirements,
    serialize_job_requirement,
    update_job_requirement,
    update_job_requirement_status,
)

router = APIRouter(prefix="/api/v1/job-requirements", tags=["job-requirements"])


@router.get("/", response_model=list[JobRequirementListItem])
def get_job_requirements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [
        serialize_job_requirement(item)
        for item in list_job_requirements(db, current_user)
    ]


@router.post("/", response_model=JobRequirementListItem, status_code=status.HTTP_201_CREATED)
def create_job_requirement_route(
    payload: JobRequirementCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return serialize_job_requirement(create_job_requirement(db, payload, current_user))


@router.get("/{requirement_id}", response_model=JobRequirementListItem)
def get_job_requirement_route(
    requirement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return serialize_job_requirement(get_job_requirement(db, requirement_id, current_user))


@router.put("/{requirement_id}", response_model=JobRequirementListItem)
def update_job_requirement_route(
    requirement_id: uuid.UUID,
    payload: JobRequirementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return serialize_job_requirement(
        update_job_requirement(db, requirement_id, payload, current_user)
    )


@router.patch("/{requirement_id}/status", response_model=JobRequirementListItem)
def patch_job_requirement_status(
    requirement_id: uuid.UUID,
    payload: JobRequirementStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return serialize_job_requirement(
        update_job_requirement_status(db, requirement_id, payload, current_user)
    )
