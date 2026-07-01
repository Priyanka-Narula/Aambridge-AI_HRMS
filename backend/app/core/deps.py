import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import ROLE_OWNER, ROLE_RECRUITER, decode_access_token, normalize_role
from app.models.user_access import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = (
        db.query(User)
        .options(joinedload(User.role), joinedload(User.recruiter))
        .filter(User.id == uuid.UUID(user_id))
        .first()
    )
    if not user:
        raise credentials_exc
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return user


def require_roles(*roles: str) -> Callable:
    allowed = {normalize_role(role) for role in roles}

    def checker(current_user: User = Depends(get_current_user)) -> User:
        role_name = normalize_role(current_user.role.name)
        if role_name not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return checker


require_owner = require_roles(ROLE_OWNER)
require_recruiter = require_roles(ROLE_RECRUITER)
require_authenticated = get_current_user
