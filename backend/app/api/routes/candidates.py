from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.candidate import Candidate
from app.api.schemas.candidate import CandidateCreate, CandidateResponse

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post(
    "/",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
):
    print("📥 create_candidate endpoint HIT")
    # optional: prevent duplicate email
    existing = (
        db.query(Candidate)
        .filter(Candidate.email == payload.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Candidate with this email already exists",
        )

    candidate = Candidate(**payload.model_dump())
    print("📥 candidate created", candidate)

    db.add(candidate)
    print("📥 candidate added to database", candidate)
    db.commit()
    db.refresh(candidate)

    return candidate