from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginRequest, TokenResponse, UserMeResponse
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user_access import User
from app.services.auth_service import authenticate_user, issue_token_for_user, serialize_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, str(payload.email), payload.password)
    return TokenResponse(access_token=issue_token_for_user(user))


@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)
