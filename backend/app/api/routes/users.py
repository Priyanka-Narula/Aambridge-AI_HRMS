import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.user import RecruiterCreateRequest, UserListItem, UserStatusUpdate
from app.core.database import get_db
from app.core.deps import require_owner
from app.models.user_access import User
from app.services.user_service import (
    create_recruiter,
    list_users,
    serialize_user_list_item,
    update_user_status,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/recruiters", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
def create_recruiter_user(
    payload: RecruiterCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    user = create_recruiter(db, payload)
    return serialize_user_list_item(user)


@router.get("/", response_model=list[UserListItem])
def get_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    return [serialize_user_list_item(user) for user in list_users(db)]


@router.patch("/{user_id}/status", response_model=UserListItem)
def patch_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    user = update_user_status(db, user_id, payload)
    return serialize_user_list_item(user)
