"""Pydantic schemas for the backend API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TopPrediction(BaseModel):
    class_id: int
    class_name: str
    confidence: float


class PlantInfo(BaseModel):
    id: int | None = None
    class_id: int
    name_en: str
    name_cn: str | None = None
    display_name: str
    description: str
    morphology: str | None = None
    habitat: str | None = None
    care_tips: list[str] = Field(default_factory=list)
    flower_language: str
    season: str
    distribution: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str


class RecognitionResponse(BaseModel):
    filename: str | None = None
    model_name: str
    checkpoint_path: str
    pred_class: int
    pred_name: str
    confidence: float
    top3: list[TopPrediction]
    plant: PlantInfo | None = None


class PlantListResponse(BaseModel):
    items: list[PlantInfo]
    total: int


class HealthResponse(BaseModel):
    status: str
    service: str
    data: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    message: str


class UserInfo(BaseModel):
    id: int
    username: str
    email: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=6, max_length=1024)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class FavoriteCreateRequest(BaseModel):
    note: str | None = Field(default=None, max_length=255)


class FavoriteItem(BaseModel):
    id: int
    plant: PlantInfo
    note: str | None = None
    created_at: datetime | None = None


class FavoriteListResponse(BaseModel):
    items: list[FavoriteItem]
    total: int


class RecognitionHistoryItem(BaseModel):
    id: int
    image_name: str | None = None
    image_path: str | None = None
    pred_class: int
    pred_name: str
    confidence: float
    top3: list[TopPrediction] = Field(default_factory=list)
    plant: PlantInfo | None = None
    created_at: datetime | None = None
    source: str | None = None


class RecognitionHistoryListResponse(BaseModel):
    items: list[RecognitionHistoryItem]
    total: int


class KnowledgeDocumentInfo(BaseModel):
    id: int
    plant_id: int | None = None
    title: str
    topic: str
    content: str
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeChunkInfo(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    chunk_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class RagQueryInfo(BaseModel):
    id: int
    query_text: str
    matched_doc_ids: list[int] = Field(default_factory=list)
    retrieval_type: str | None = None
    answer_text: str | None = None
    created_at: datetime | None = None


class RagMessageInfo(BaseModel):
    id: int
    session_id: int
    role: Literal["user", "assistant"]
    content: str
    related_plant_id: int | None = None
    retrieval_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class RagSessionInfo(BaseModel):
    id: int
    user_id: int | None = None
    title: str
    current_plant_id: int | None = None
    current_plant: PlantInfo | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_message_at: datetime | None = None
    messages: list[RagMessageInfo] = Field(default_factory=list)


class RagSessionListResponse(BaseModel):
    items: list[RagSessionInfo]
    total: int


class RagChatMemoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class RagChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: int | None = None
    plant_id: int | None = None
    persist: bool = True
    recent_messages: list[RagChatMemoryMessage] = Field(default_factory=list)


class RagChatResponse(BaseModel):
    session_id: int | None = None
    title: str | None = None
    answer: str
    provider: str
    plant: PlantInfo | None = None
    retrieved_plant_context: dict[str, Any] = Field(default_factory=dict)
    recent_messages: list[RagMessageInfo] = Field(default_factory=list)
