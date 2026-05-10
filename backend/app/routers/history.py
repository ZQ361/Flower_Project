"""Recognition history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..dependencies import get_current_user
from ..db.session import get_db
from ..schemas import MessageResponse, RecognitionHistoryItem, RecognitionHistoryListResponse
from ..services.history_service import delete_history_item, list_history_items


router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=RecognitionHistoryListResponse)
def read_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    limit: int | None = Query(default=50, ge=1, le=200),
) -> RecognitionHistoryListResponse:
    items = list_history_items(db, user_id=current_user.id, limit=limit)
    return RecognitionHistoryListResponse(
        items=[RecognitionHistoryItem(**item) for item in items],
        total=len(items),
    )


@router.delete("/{history_id}", response_model=MessageResponse)
def remove_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MessageResponse:
    deleted = delete_history_item(db, user_id=current_user.id, history_id=history_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found")
    return MessageResponse(message="History item removed")
