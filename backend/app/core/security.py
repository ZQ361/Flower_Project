"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .settings import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY


# Use PBKDF2 to avoid bcrypt 5.0.0 / passlib backend compatibility issues and
# the 72-byte bcrypt input limit.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire_minutes = expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": int(expire.timestamp())}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if not isinstance(subject, str):
            return None
        return subject
    except JWTError:
        return None
