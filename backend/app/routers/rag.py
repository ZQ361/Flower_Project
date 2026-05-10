"""Pseudo-RAG endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_optional_current_user
from ..db.crud import rag_session_to_dict
from ..db.session import get_db
from ..schemas import (
    MessageResponse,
    PlantInfo,
    RagChatRequest,
    RagChatResponse,
    RagMessageInfo,
    RagSessionInfo,
    RagSessionListResponse,
)
from ..services.rag_service import answer_question, stream_answer_events
from ..db.crud import delete_user_rag_session, get_user_rag_session, list_user_rag_sessions


router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/sessions", response_model=RagSessionListResponse)
def read_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> RagSessionListResponse:
    items = list_user_rag_sessions(db, user_id=current_user.id)
    return RagSessionListResponse(items=[RagSessionInfo(**item) for item in items], total=len(items))


@router.post("/chat", response_model=RagChatResponse)
def chat_with_rag(
    payload: RagChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> RagChatResponse:
    try:
        result = answer_question(
            db,
            question=payload.question,
            plant_id=payload.plant_id,
            session_id=payload.session_id,
            current_user_id=current_user.id if current_user else None,
            persist=payload.persist,
            recent_messages=[item.model_dump() for item in payload.recent_messages],
        )
    except ValueError as exc:
        message = str(exc)
        if message == "Plant not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        if message == "Session not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    session_payload = result.session
    session = RagSessionInfo(**session_payload) if session_payload else None
    return RagChatResponse(
        session_id=session.id if session else None,
        title=session.title if session else None,
        answer=result.answer,
        provider=result.provider,
        plant=PlantInfo(**result.plant) if result.plant else None,
        retrieved_plant_context=result.retrieved_plant_context,
        recent_messages=[RagMessageInfo(**item) for item in result.recent_messages],
    )


@router.post("/chat/stream")
def stream_chat_with_rag(
    payload: RagChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> StreamingResponse:
    def event_stream():
        try:
            events = stream_answer_events(
                db,
                question=payload.question,
                plant_id=payload.plant_id,
                session_id=payload.session_id,
                current_user_id=current_user.id if current_user else None,
                persist=payload.persist,
                recent_messages=[item.model_dump() for item in payload.recent_messages],
            )
            for event in events:
                yield json.dumps(jsonable_encoder(event), ensure_ascii=False) + "\n"
        except ValueError as exc:
            yield json.dumps({"type": "error", "message": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}", response_model=RagSessionInfo)
def read_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> RagSessionInfo:
    session = get_user_rag_session(db, user_id=current_user.id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return RagSessionInfo(**rag_session_to_dict(session, include_messages=True))


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def remove_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MessageResponse:
    deleted = delete_user_rag_session(db, user_id=current_user.id, session_id=session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return MessageResponse(message="Session removed")
