import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas.pipeline import (
    CandidateStageHistoryResponse,
    EmailStatusResponse,
    PipelineBoardResponse,
    PipelineCardResponse,
    PipelineMoveRequest,
    ShareApprovedRequest,
    ShareApprovedResponse,
    ShortlistRequest,
    StageHistoryItem,
)
from app.core.database import get_db
from app.core.deps import get_current_user, require_owner
from app.models.user_access import User
from app.services import pipeline_service

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


@router.get("/board", response_model=PipelineBoardResponse)
def pipeline_board(
    client_id: uuid.UUID | None = None,
    job_requirement_id: uuid.UUID | None = None,
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return pipeline_service.get_pipeline_board(
        db,
        current_user,
        client_id=client_id,
        job_requirement_id=job_requirement_id,
        search=search,
    )


@router.post("/shortlist", response_model=list[PipelineCardResponse])
def shortlist_candidates(
    payload: ShortlistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return pipeline_service.shortlist_applications(
        db,
        payload.application_ids,
        current_user,
        remarks=payload.remarks,
    )


@router.patch("/applications/{app_id}/stage", response_model=PipelineCardResponse)
def move_stage(
    app_id: uuid.UUID,
    payload: PipelineMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return pipeline_service.move_application_stage(
        db,
        app_id,
        payload.stage_name,
        current_user,
        remarks=payload.remarks,
        offered_ctc=payload.offered_ctc,
        joining_date=payload.joining_date,
        joined_date=payload.joined_date,
        revenue_generated=payload.revenue_generated,
    )


@router.get("/applications/{app_id}/history", response_model=list[StageHistoryItem])
def application_history(
    app_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return pipeline_service.get_stage_history(db, app_id, current_user)


@router.get(
    "/candidates/{candidate_id}/history",
    response_model=CandidateStageHistoryResponse,
)
def candidate_stage_history(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return pipeline_service.get_candidate_stage_history(db, candidate_id, current_user)


@router.get("/email-status", response_model=EmailStatusResponse)
def email_status(
    current_user: User = Depends(require_owner),
):
    return pipeline_service.get_email_status()


@router.post(
    "/share-approved/{client_id}",
    response_model=ShareApprovedResponse,
)
def share_approved(
    client_id: uuid.UUID,
    payload: ShareApprovedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return pipeline_service.share_approved_with_client(
        db,
        client_id,
        current_user,
        to_emails=payload.to_emails,
        subject=payload.subject,
        message=payload.message,
        application_ids=payload.application_ids,
    )
