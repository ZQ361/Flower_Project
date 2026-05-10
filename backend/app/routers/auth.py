"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.crud import user_to_dict
from ..db.session import get_db
from ..dependencies import get_current_user
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserInfo
from ..services.auth_service import authenticate_user, build_token_for_user, register_user


router = APIRouter(prefix="/auth", tags=["auth"])


def _build_user_info(user_dict: dict) -> UserInfo:
    return UserInfo(**user_dict)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    username = payload.username.strip()
    email = payload.email.strip() if payload.email else None

    try:
        user = register_user(db, username=username, email=email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = build_token_for_user(user.id)
    return TokenResponse(access_token=token, user=_build_user_info(user_to_dict(user)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, username=payload.username.strip(), password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = build_token_for_user(user.id)
    return TokenResponse(access_token=token, user=_build_user_info(user_to_dict(user)))


@router.get("/me", response_model=UserInfo)
def read_current_user(current_user=Depends(get_current_user)) -> UserInfo:
    return _build_user_info(user_to_dict(current_user))
