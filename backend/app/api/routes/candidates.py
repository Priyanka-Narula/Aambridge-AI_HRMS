import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate
from app.core.database import get_db
from app.services.candidate_service import (
    create_candidate_record,
    delete_candidate_record,
    get_candidate_or_404,
    list_candidates,
    serialize_candidate,
    update_candidate_record,
)

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.get("/", response_model=list[CandidateResponse])
def get_candidates(db: Session = Depends(get_db)):
    candidates = list_candidates(db)
    return [serialize_candidate(c) for c in candidates]


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: uuid.UUID, db: Session = Depends(get_db)):
    candidate = get_candidate_or_404(db, candidate_id)
    return serialize_candidate(candidate)


@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)):
    candidate = create_candidate_record(db, payload)
    return serialize_candidate(candidate)


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
):
    candidate = update_candidate_record(db, candidate_id, payload)
    return serialize_candidate(candidate)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: uuid.UUID, db: Session = Depends(get_db)):
    delete_candidate_record(db, candidate_id)
