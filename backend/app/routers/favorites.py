"""Favorite endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user
from ..db.crud import favorite_to_dict
from ..db.session import get_db
from ..schemas import FavoriteCreateRequest, FavoriteItem, FavoriteListResponse, MessageResponse
from ..services.favorite_service import add_user_favorite, delete_user_favorite, list_user_favorite_items


router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=FavoriteListResponse)
def read_favorites(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FavoriteListResponse:
    items = list_user_favorite_items(db, user_id=current_user.id)
    return FavoriteListResponse(items=[FavoriteItem(**item) for item in items], total=len(items))


@router.post("/{plant_id}", response_model=FavoriteItem)
def create_favorite(
    plant_id: int,
    payload: FavoriteCreateRequest | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FavoriteItem:
    try:
        favorite = add_user_favorite(
            db,
            user_id=current_user.id,
            plant_id=plant_id,
            note=payload.note if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FavoriteItem(**favorite_to_dict(favorite))


@router.delete("/{plant_id}", response_model=MessageResponse)
def remove_favorite(
    plant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MessageResponse:
    deleted = delete_user_favorite(db, user_id=current_user.id, plant_id=plant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")
    return MessageResponse(message="Favorite removed")
