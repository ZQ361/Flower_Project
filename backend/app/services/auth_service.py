"""Authentication business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..core.security import create_access_token, get_password_hash, verify_password
from ..db.crud import create_user, get_user_by_email, get_user_by_id, get_user_by_username, update_last_login


def register_user(db: Session, *, username: str, email: str | None, password: str):
    if get_user_by_username(db, username) is not None:
        raise ValueError("Username already exists")
    if email and get_user_by_email(db, email) is not None:
        raise ValueError("Email already exists")

    password_hash = get_password_hash(password)
    return create_user(db, username=username, email=email, password_hash=password_hash)


def authenticate_user(db: Session, *, username: str, password: str):
    user = get_user_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return update_last_login(db, user)


def build_token_for_user(user_id: int) -> str:
    return create_access_token(str(user_id))


def get_user_info(db: Session, user_id: int):
    return get_user_by_id(db, user_id)
