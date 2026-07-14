import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.schemas.submission import (
    CandidateSubmissionResponse,
    OwnerApprovalRequest,
    OwnerDashboardClient,
)
from app.core.database import get_db
from app.core.deps import get_current_user, require_owner
from app.models.user_access import User
from app.services.submission_service import (
    approve_submission,
    generate_bulk_approved_client_excel,
    generate_submission_excel,
    get_owner_dashboard,
    serialize_submission,
)

router = APIRouter(prefix="/api/v1/submissions", tags=["submissions"])


@router.patch("/{app_id}/approve", response_model=CandidateSubmissionResponse)
def approve_submission_route(
    app_id: uuid.UUID,
    payload: OwnerApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    from app.services.submission_service import (
        _load_application_with_full_relations,
        _load_job_requirement,
    )
    from app.models.candidate import Candidate as CandidateModel

    app = approve_submission(db, app_id, payload.action, current_user)
    jr = _load_job_requirement(db, app.job_requirement_id)
    candidate = db.query(CandidateModel).filter(CandidateModel.id == app.candidate_id).first()
    return serialize_submission(app, jr, candidate)


@router.get("/{app_id}/download")
def download_submission_route(
    app_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    excel_bytes, filename = generate_submission_excel(db, app_id, current_user)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/owner/download-approved/{client_id}")
def download_approved_client_route(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    excel_bytes, filename = generate_bulk_approved_client_excel(db, client_id, current_user)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/owner/dashboard", response_model=list[OwnerDashboardClient])
def owner_dashboard_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return get_owner_dashboard(db, current_user)
