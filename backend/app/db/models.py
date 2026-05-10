"""SQLAlchemy models for the flower platform."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    recognition_history: Mapped[list["RecognitionHistory"]] = relationship(back_populates="user")
    browse_history: Mapped[list["BrowseHistory"]] = relationship(back_populates="user")
    rag_queries: Mapped[list["RagQuery"]] = relationship(back_populates="user")
    rag_sessions: Mapped[list["RagSession"]] = relationship(back_populates="user")


class PlantSpecies(Base):
    __tablename__ = "plant_species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_cn: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    morphology: Mapped[str | None] = mapped_column(Text, nullable=True)
    habitat: Mapped[str | None] = mapped_column(Text, nullable=True)
    care_tips: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    flower_language: Mapped[str] = mapped_column(Text, nullable=False)
    season: Mapped[str] = mapped_column(String(128), nullable=False)
    distribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="auto-generated", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="plant")
    recognition_history: Mapped[list["RecognitionHistory"]] = relationship(back_populates="plant")
    browse_history: Mapped[list["BrowseHistory"]] = relationship(back_populates="plant")
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="plant")
    rag_sessions: Mapped[list["RagSession"]] = relationship(back_populates="current_plant")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "plant_id", name="uq_user_plant_favorite"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id", ondelete="CASCADE"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="favorites")
    plant: Mapped[PlantSpecies] = relationship(back_populates="favorites")


class RecognitionHistory(Base):
    __tablename__ = "recognition_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plant_species.id", ondelete="SET NULL"), nullable=True)
    image_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pred_class: Mapped[int] = mapped_column(Integer, nullable=False)
    pred_name: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top3_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="web", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped[User | None] = relationship(back_populates="recognition_history")
    plant: Mapped[PlantSpecies | None] = relationship(back_populates="recognition_history")


class BrowseHistory(Base):
    __tablename__ = "browse_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plant_species.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="browse_history")
    plant: Mapped[PlantSpecies] = relationship(back_populates="browse_history")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plant_species.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    plant: Mapped[PlantSpecies | None] = relationship(back_populates="knowledge_documents")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")


class RagQuery(Base):
    __tablename__ = "rag_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    matched_doc_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    retrieval_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped[User | None] = relationship(back_populates="rag_queries")


class RagSession(Base):
    __tablename__ = "rag_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="花卉问答", nullable=False)
    current_plant_id: Mapped[int | None] = mapped_column(
        ForeignKey("plant_species.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User | None] = relationship(back_populates="rag_sessions")
    current_plant: Mapped[PlantSpecies | None] = relationship(back_populates="rag_sessions")
    messages: Mapped[list["RagMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="RagMessage.created_at",
    )


class RagMessage(Base):
    __tablename__ = "rag_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("rag_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    related_plant_id: Mapped[int | None] = mapped_column(
        ForeignKey("plant_species.id", ondelete="SET NULL"),
        nullable=True,
    )
    retrieval_context_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    session: Mapped[RagSession] = relationship(back_populates="messages")
    related_plant: Mapped[PlantSpecies | None] = relationship()
