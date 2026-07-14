from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
    UserMeResponse,
    UserMeUpdateRequest,
)
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user_access import User
from app.services.auth_service import (
    authenticate_user,
    change_password,
    issue_token_for_user,
    serialize_user,
    update_me,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, str(payload.email), payload.password)
    return TokenResponse(access_token=issue_token_for_user(user))


@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


@router.put("/me", response_model=UserMeResponse)
def update_my_profile(
    payload: UserMeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = update_me(db, current_user, payload.model_dump())
    return serialize_user(updated)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def update_my_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    change_password(db, current_user, payload.current_password, payload.new_password)
    return None
