import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.schemas.job_requirement import (
    JobRequirementCreateRequest,
    JobRequirementListItem,
    JobRequirementStatusUpdate,
    JobRequirementUpdateRequest,
)
from app.api.schemas.submission import CandidateSubmissionResponse, CandidateSubmitRequest
from app.core.database import get_db
from app.core.deps import get_current_user, require_owner
from app.models.user_access import User
from app.services.job_requirement_service import (
    create_job_requirement,
    get_job_pipeline_metric,
    get_job_pipeline_metrics,
    get_job_requirement,
    list_job_requirements,
    serialize_job_requirement,
    update_job_requirement,
    update_job_requirement_status,
)
from app.services.submission_service import (
    generate_bulk_job_excel,
    list_submissions,
    serialize_submission,
    submit_candidate,
)

router = APIRouter(prefix="/api/v1/job-requirements", tags=["job-requirements"])


@router.get("/", response_model=list[JobRequirementListItem])
def get_job_requirements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = list_job_requirements(db, current_user)
    metrics = get_job_pipeline_metrics(db, {item.id for item in items})
    return [
        serialize_job_requirement(item, metrics[item.id])
        for item in items
    ]


@router.post("/", response_model=JobRequirementListItem, status_code=status.HTTP_201_CREATED)
def create_job_requirement_route(
    payload: JobRequirementCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    item = create_job_requirement(db, payload, current_user)
    return serialize_job_requirement(item, get_job_pipeline_metric(db, item.id))


@router.get("/{requirement_id}", response_model=JobRequirementListItem)
def get_job_requirement_route(
    requirement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_job_requirement(db, requirement_id, current_user)
    return serialize_job_requirement(item, get_job_pipeline_metric(db, item.id))


@router.put("/{requirement_id}", response_model=JobRequirementListItem)
def update_job_requirement_route(
    requirement_id: uuid.UUID,
    payload: JobRequirementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    item = update_job_requirement(db, requirement_id, payload, current_user)
    return serialize_job_requirement(item, get_job_pipeline_metric(db, item.id))


@router.patch("/{requirement_id}/status", response_model=JobRequirementListItem)
def patch_job_requirement_status(
    requirement_id: uuid.UUID,
    payload: JobRequirementStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    item = update_job_requirement_status(db, requirement_id, payload, current_user)
    return serialize_job_requirement(item, get_job_pipeline_metric(db, item.id))


@router.post(
    "/{requirement_id}/submissions",
    response_model=CandidateSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_candidate_route(
    requirement_id: uuid.UUID,
    payload: CandidateSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.submission_service import _load_job_requirement
    from app.models.candidate import Candidate as CandidateModel

    app = submit_candidate(
        db, requirement_id, payload.candidate_id, current_user,
        submission_data=payload.submission_data,
    )
    jr_obj = _load_job_requirement(db, requirement_id)
    candidate = db.query(CandidateModel).filter(CandidateModel.id == app.candidate_id).first()
    return serialize_submission(app, jr_obj, candidate)


@router.get("/{requirement_id}/submissions", response_model=list[CandidateSubmissionResponse])
def list_submissions_route(
    requirement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.submission_service import _load_job_requirement
    from app.models.candidate import Candidate as CandidateModel

    jr_obj = _load_job_requirement(db, requirement_id)
    apps = list_submissions(db, requirement_id, current_user)

    cand_ids = [a.candidate_id for a in apps]
    cand_map = {}
    if cand_ids:
        for c in db.query(CandidateModel).filter(CandidateModel.id.in_(cand_ids)).all():
            cand_map[c.id] = c

    return [serialize_submission(app, jr_obj, cand_map.get(app.candidate_id)) for app in apps]


@router.get("/{requirement_id}/submissions/download-all")
def download_all_submissions_route(
    requirement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    excel_bytes, filename = generate_bulk_job_excel(db, requirement_id, current_user)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
