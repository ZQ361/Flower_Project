"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .core.security import decode_access_token
from .db.crud import get_user_by_id
from .db.session import get_db


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "bearer "
    if not authorization.lower().startswith(prefix):
        return None
    return authorization[len(prefix) :].strip() or None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = _extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from exc

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_optional_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = _extract_bearer_token(authorization)
    if token is None:
        return None

    subject = decode_access_token(token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from exc

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
