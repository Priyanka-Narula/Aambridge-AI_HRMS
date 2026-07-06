import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas.client import (
    ClientCreateRequest,
    ClientListItem,
    ClientStatusUpdate,
    ClientUpdateRequest,
)
from app.core.database import get_db
from app.core.deps import require_owner
from app.models.user_access import User
from app.services.client_service import (
    create_client,
    get_client,
    list_clients,
    serialize_client,
    update_client,
    update_client_status,
)

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("/", response_model=list[ClientListItem])
def get_clients(
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    return [serialize_client(c) for c in list_clients(db)]


@router.post("/", response_model=ClientListItem, status_code=status.HTTP_201_CREATED)
def create_client_route(
    payload: ClientCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    return serialize_client(create_client(db, payload))


@router.get("/{client_id}", response_model=ClientListItem)
def get_client_route(
    client_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    return serialize_client(get_client(db, client_id))


@router.put("/{client_id}", response_model=ClientListItem)
def update_client_route(
    client_id: uuid.UUID,
    payload: ClientUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    return serialize_client(update_client(db, client_id, payload))


@router.patch("/{client_id}/status", response_model=ClientListItem)
def patch_client_status(
    client_id: uuid.UUID,
    payload: ClientStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_owner),
):
    return serialize_client(update_client_status(db, client_id, payload))
