"""Data access helpers for the flower platform."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Favorite,
    KnowledgeChunk,
    KnowledgeDocument,
    PlantSpecies,
    RagMessage,
    RagQuery,
    RagSession,
    RecognitionHistory,
    User,
)

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def to_beijing_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(SHANGHAI_TZ)


def plant_to_dict(plant: PlantSpecies) -> dict[str, Any]:
    return {
        "id": plant.id,
        "class_id": plant.class_id,
        "name_en": plant.name_en,
        "name_cn": plant.name_cn,
        "display_name": plant.display_name,
        "description": plant.description,
        "morphology": plant.morphology,
        "habitat": plant.habitat,
        "care_tips": list(plant.care_tips or []),
        "flower_language": plant.flower_language,
        "season": plant.season,
        "distribution": plant.distribution,
        "tags": list(plant.tags or []),
        "source": plant.source,
    }


def user_to_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "created_at": to_beijing_time(user.created_at),
        "last_login_at": to_beijing_time(user.last_login_at),
    }


def favorite_to_dict(favorite: Favorite) -> dict[str, Any]:
    return {
        "id": favorite.id,
        "note": favorite.note,
        "created_at": to_beijing_time(favorite.created_at),
        "plant": plant_to_dict(favorite.plant),
    }


def history_to_dict(history: RecognitionHistory) -> dict[str, Any]:
    return {
        "id": history.id,
        "image_name": history.image_name,
        "image_path": history.image_path,
        "pred_class": history.pred_class,
        "pred_name": history.pred_name,
        "confidence": history.confidence,
        "top3": list(history.top3_json or []),
        "source": history.source,
        "created_at": to_beijing_time(history.created_at),
        "plant": plant_to_dict(history.plant) if history.plant else None,
    }


def knowledge_document_to_dict(document: KnowledgeDocument) -> dict[str, Any]:
    return {
        "id": document.id,
        "plant_id": document.plant_id,
        "title": document.title,
        "topic": document.topic,
        "content": document.content,
        "keywords": list(document.keywords or []),
        "tags": list(document.tags or []),
        "source": document.source,
        "status": document.status,
        "created_at": to_beijing_time(document.created_at),
        "updated_at": to_beijing_time(document.updated_at),
    }


def knowledge_chunk_to_dict(chunk: KnowledgeChunk) -> dict[str, Any]:
    return {
        "id": chunk.id,
        "document_id": chunk.document_id,
        "chunk_index": chunk.chunk_index,
        "chunk_text": chunk.chunk_text,
        "metadata": dict(chunk.metadata_json or {}),
        "created_at": to_beijing_time(chunk.created_at),
    }


def rag_query_to_dict(query: RagQuery) -> dict[str, Any]:
    return {
        "id": query.id,
        "query_text": query.query_text,
        "matched_doc_ids": list(query.matched_doc_ids or []),
        "retrieval_type": query.retrieval_type,
        "answer_text": query.answer_text,
        "created_at": to_beijing_time(query.created_at),
    }


def rag_message_to_dict(message: RagMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role,
        "content": message.content,
        "related_plant_id": message.related_plant_id,
        "retrieval_context": dict(message.retrieval_context_json or {}),
        "created_at": to_beijing_time(message.created_at),
    }


def rag_session_to_dict(session: RagSession, include_messages: bool = False) -> dict[str, Any]:
    payload = {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "current_plant_id": session.current_plant_id,
        "created_at": to_beijing_time(session.created_at),
        "updated_at": to_beijing_time(session.updated_at),
        "last_message_at": to_beijing_time(session.last_message_at),
        "current_plant": plant_to_dict(session.current_plant) if session.current_plant else None,
    }
    if include_messages:
        payload["messages"] = [rag_message_to_dict(item) for item in session.messages]
    return payload


def get_plant_by_class_id(db: Session, class_id: int) -> PlantSpecies | None:
    stmt = select(PlantSpecies).where(PlantSpecies.class_id == class_id)
    return db.scalar(stmt)


def get_plant_by_id(db: Session, plant_id: int) -> PlantSpecies | None:
    stmt = select(PlantSpecies).where(PlantSpecies.id == plant_id)
    return db.scalar(stmt)


def list_plants(db: Session, query: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    stmt = select(PlantSpecies).order_by(PlantSpecies.class_id)
    plants = list(db.scalars(stmt).all())

    if query:
        normalized = query.strip().lower()
        filtered: list[PlantSpecies] = []
        for plant in plants:
            haystack = " ".join(
                [
                    str(plant.class_id),
                    plant.name_en or "",
                    plant.name_cn or "",
                    plant.display_name or "",
                    plant.description or "",
                    plant.morphology or "",
                    plant.habitat or "",
                    plant.flower_language or "",
                    plant.season or "",
                    plant.distribution or "",
                    " ".join(plant.tags or []),
                ]
            ).lower()
            if normalized in haystack:
                filtered.append(plant)
        plants = filtered

    if limit is not None:
        plants = plants[:limit]

    return [plant_to_dict(plant) for plant in plants]


def create_user(db: Session, *, username: str, email: str | None, password_hash: str) -> User:
    user = User(username=username, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return db.scalar(stmt)


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def update_last_login(db: Session, user: User) -> User:
    from datetime import datetime

    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_user_favorites(db: Session, user_id: int) -> list[dict[str, Any]]:
    stmt = select(Favorite).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc())
    favorites = db.scalars(stmt).all()
    return [favorite_to_dict(item) for item in favorites]


def get_user_favorite(db: Session, user_id: int, plant_id: int) -> Favorite | None:
    stmt = select(Favorite).where(Favorite.user_id == user_id, Favorite.plant_id == plant_id)
    return db.scalar(stmt)


def add_favorite(db: Session, *, user_id: int, plant_id: int, note: str | None = None) -> Favorite:
    favorite = get_user_favorite(db, user_id, plant_id)
    if favorite is not None:
        favorite.note = note if note is not None else favorite.note
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite

    favorite = Favorite(user_id=user_id, plant_id=plant_id, note=note)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, *, user_id: int, plant_id: int) -> bool:
    favorite = get_user_favorite(db, user_id, plant_id)
    if favorite is None:
        return False
    db.delete(favorite)
    db.commit()
    return True


def list_user_history(db: Session, user_id: int, limit: int | None = None) -> list[dict[str, Any]]:
    stmt = (
        select(RecognitionHistory)
        .where(RecognitionHistory.user_id == user_id)
        .order_by(RecognitionHistory.created_at.desc())
    )
    history_items = list(db.scalars(stmt).all())
    if limit is not None:
        history_items = history_items[:limit]
    return [history_to_dict(item) for item in history_items]


def get_user_history_item(db: Session, user_id: int, history_id: int) -> RecognitionHistory | None:
    stmt = select(RecognitionHistory).where(
        RecognitionHistory.id == history_id,
        RecognitionHistory.user_id == user_id,
    )
    return db.scalar(stmt)


def remove_user_history_item(db: Session, *, user_id: int, history_id: int) -> bool:
    history_item = get_user_history_item(db, user_id, history_id)
    if history_item is None:
        return False
    db.delete(history_item)
    db.commit()
    return True


def create_recognition_history(
    db: Session,
    *,
    user_id: int | None,
    plant_id: int | None,
    image_name: str | None,
    image_path: str | None,
    pred_class: int,
    pred_name: str,
    confidence: float,
    top3: list[dict[str, Any]],
    source: str = "web",
) -> RecognitionHistory:
    history = RecognitionHistory(
        user_id=user_id,
        plant_id=plant_id,
        image_name=image_name,
        image_path=image_path,
        pred_class=pred_class,
        pred_name=pred_name,
        confidence=confidence,
        top3_json=top3,
        source=source,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def list_knowledge_documents(db: Session, plant_id: int | None = None) -> list[dict[str, Any]]:
    stmt = select(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc())
    if plant_id is not None:
        stmt = stmt.where(KnowledgeDocument.plant_id == plant_id)
    return [knowledge_document_to_dict(item) for item in db.scalars(stmt).all()]


def list_knowledge_chunks(db: Session, document_id: int | None = None) -> list[dict[str, Any]]:
    stmt = select(KnowledgeChunk).order_by(KnowledgeChunk.chunk_index.asc())
    if document_id is not None:
        stmt = stmt.where(KnowledgeChunk.document_id == document_id)
    return [knowledge_chunk_to_dict(item) for item in db.scalars(stmt).all()]


def create_rag_query(
    db: Session,
    *,
    user_id: int | None,
    query_text: str,
    matched_doc_ids: list[int],
    retrieval_type: str | None,
    answer_text: str | None,
) -> RagQuery:
    record = RagQuery(
        user_id=user_id,
        query_text=query_text,
        matched_doc_ids=matched_doc_ids,
        retrieval_type=retrieval_type,
        answer_text=answer_text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_rag_queries(db: Session, user_id: int | None = None) -> list[dict[str, Any]]:
    stmt = select(RagQuery).order_by(RagQuery.created_at.desc())
    if user_id is not None:
        stmt = stmt.where(RagQuery.user_id == user_id)
    return [rag_query_to_dict(item) for item in db.scalars(stmt).all()]


def create_rag_session(
    db: Session,
    *,
    user_id: int | None,
    title: str,
    current_plant_id: int | None = None,
) -> RagSession:
    session = RagSession(user_id=user_id, title=title, current_plant_id=current_plant_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_user_rag_sessions(db: Session, user_id: int) -> list[dict[str, Any]]:
    stmt = (
        select(RagSession)
        .where(RagSession.user_id == user_id)
        .order_by(RagSession.last_message_at.desc().nullslast(), RagSession.updated_at.desc())
    )
    sessions = db.scalars(stmt).all()
    return [rag_session_to_dict(item) for item in sessions]


def get_user_rag_session(db: Session, *, user_id: int, session_id: int) -> RagSession | None:
    stmt = select(RagSession).where(RagSession.id == session_id, RagSession.user_id == user_id)
    return db.scalar(stmt)


def delete_user_rag_session(db: Session, *, user_id: int, session_id: int) -> bool:
    session = get_user_rag_session(db, user_id=user_id, session_id=session_id)
    if session is None:
        return False
    db.delete(session)
    db.commit()
    return True


def get_rag_session_by_id(db: Session, session_id: int) -> RagSession | None:
    stmt = select(RagSession).where(RagSession.id == session_id)
    return db.scalar(stmt)


def update_rag_session(
    db: Session,
    session: RagSession,
    *,
    title: str | None = None,
    current_plant_id: int | None = None,
    last_message_at: datetime | None = None,
) -> RagSession:
    if title is not None:
        session.title = title
    if current_plant_id is not None:
        session.current_plant_id = current_plant_id
    if last_message_at is not None:
        session.last_message_at = last_message_at
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_rag_messages(db: Session, session_id: int, limit: int | None = None) -> list[dict[str, Any]]:
    stmt = select(RagMessage).where(RagMessage.session_id == session_id).order_by(RagMessage.created_at.asc())
    messages = list(db.scalars(stmt).all())
    if limit is not None:
        messages = messages[-limit:]
    return [rag_message_to_dict(item) for item in messages]


def create_rag_message(
    db: Session,
    *,
    session_id: int,
    role: str,
    content: str,
    related_plant_id: int | None = None,
    retrieval_context: dict[str, Any] | None = None,
) -> RagMessage:
    message = RagMessage(
        session_id=session_id,
        role=role,
        content=content,
        related_plant_id=related_plant_id,
        retrieval_context_json=retrieval_context or {},
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
