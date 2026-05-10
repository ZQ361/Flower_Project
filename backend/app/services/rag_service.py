"""Pseudo-RAG service for flower Q&A."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator
from urllib import error, request

from sqlalchemy.orm import Session

from ..core import settings
from ..db.crud import (
    create_rag_message,
    create_rag_query,
    create_rag_session,
    get_plant_by_id,
    get_user_rag_session,
    list_rag_messages,
    plant_to_dict,
    rag_session_to_dict,
    update_rag_session,
)


@dataclass(slots=True)
class RagAnswerResult:
    session: dict[str, Any] | None
    answer: str
    provider: str
    plant: dict[str, Any] | None
    retrieved_plant_context: dict[str, Any]
    recent_messages: list[dict[str, Any]]


def _truncate_text(value: str, max_length: int = 64) -> str:
    text = value.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def _join_list(items: list[str], separator: str = "；") -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return separator.join(cleaned)


def _build_session_title(plant: dict[str, Any] | None, question: str) -> str:
    if plant and plant.get("display_name"):
        return f"{plant['display_name']}问答"
    return _truncate_text(question, 18) or "花卉问答"


def _build_plant_context(plant: dict[str, Any] | None) -> str:
    if not plant:
        return "当前未绑定具体花卉。"

    care_tips = plant.get("care_tips") or []
    tags = plant.get("tags") or []
    parts = [
        f"花名：{plant.get('display_name') or plant.get('name_cn') or plant.get('name_en')}",
        f"中文名：{plant.get('name_cn') or plant.get('display_name') or plant.get('name_en')}",
        f"英文名：{plant.get('name_en') or '-'}",
        f"简介：{plant.get('description') or '-'}",
        f"形态特征：{plant.get('morphology') or '-'}",
        f"生长环境：{plant.get('habitat') or '-'}",
        f"养护建议：{_join_list(care_tips) or '-'}",
        f"花语：{plant.get('flower_language') or '-'}",
        f"花期：{plant.get('season') or '-'}",
        f"分布：{plant.get('distribution') or '-'}",
        f"标签：{_join_list(tags, '，') or '-'}",
    ]
    return "\n".join(parts)


def _normalize_memory_messages(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items:
        role = str(item.get("role") or "").strip().lower()
        content = str(item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def _build_prompt_messages(
    *,
    question: str,
    plant: dict[str, Any] | None,
    memory_messages: list[dict[str, str]],
) -> list[dict[str, str]]:
    system_prompt = (
        "你是花卉识别与科普系统的智能问答助手。"
        "你需要用简洁、准确、自然的中文回答用户问题，避免编造不确定的信息。"
        "如果资料不足，要明确说明，并给出可操作的建议。"
        "回答应优先围绕当前识别到的花卉及其科普信息展开。"
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"花卉资料：\n{_build_plant_context(plant)}"},
    ]
    messages.extend(memory_messages)
    messages.append({"role": "user", "content": question.strip()})
    return messages


def _fallback_answer(question: str, plant: dict[str, Any] | None) -> str:
    if plant:
        title = plant.get("display_name") or plant.get("name_cn") or plant.get("name_en") or "这朵花"
        description = plant.get("description") or "当前资料中没有更详细的简介。"
        flower_language = plant.get("flower_language") or "当前资料中没有明确花语。"
        season = plant.get("season") or "当前资料中没有明确花期。"
        care_tips = plant.get("care_tips") or []
        care_text = _join_list(care_tips) if care_tips else "当前资料中没有细化养护建议。"
        return (
            f"根据当前资料，这朵花是「{title}」。\n"
            f"简介：{description}\n"
            f"花语：{flower_language}\n"
            f"花期：{season}\n"
            f"养护建议：{care_text}\n"
            f"针对你的问题“{question.strip()}”，建议结合光照、浇水和摆放环境进一步判断。"
        )

    return (
        f"我先根据你的问题“{question.strip()}”给出一个通用建议。"
        "如果你能补充花名或识别结果，我可以把回答收敛到具体花卉。"
    )


def _call_bailian_chat_completion(messages: list[dict[str, str]]) -> str:
    if not settings.BAILIAN_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    payload = {
        "model": settings.BAILIAN_MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{settings.BAILIAN_BASE_URL.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.BAILIAN_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=settings.BAILIAN_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - network/runtime dependent
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"DashScope HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:  # pragma: no cover - network/runtime dependent
        raise RuntimeError(f"DashScope connection failed: {exc.reason}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("DashScope response missing choices")

    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise RuntimeError("DashScope response missing assistant content")
    return content


def _call_bailian_chat_completion_stream(messages: list[dict[str, str]]) -> Iterator[str]:
    if not settings.BAILIAN_API_KEY:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    payload = {
        "model": settings.BAILIAN_MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "stream": True,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{settings.BAILIAN_BASE_URL.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.BAILIAN_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=settings.BAILIAN_TIMEOUT_SECONDS) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                choices = data.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    yield content
                    continue
                message = choices[0].get("message") or {}
                content = message.get("content")
                if content:
                    yield content
    except error.HTTPError as exc:  # pragma: no cover - network/runtime dependent
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"DashScope HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:  # pragma: no cover - network/runtime dependent
        raise RuntimeError(f"DashScope connection failed: {exc.reason}") from exc


def _iter_text_chunks(text: str, chunk_size: int = 12) -> Iterator[str]:
    for index in range(0, len(text), chunk_size):
        yield text[index : index + chunk_size]


def _resolve_plant(db: Session, plant_id: int | None) -> dict[str, Any] | None:
    if plant_id is None:
        return None
    plant = get_plant_by_id(db, plant_id)
    if plant is None:
        raise ValueError("Plant not found")
    return plant_to_dict(plant)


def answer_question(
    db: Session,
    *,
    question: str,
    plant_id: int | None = None,
    session_id: int | None = None,
    current_user_id: int | None = None,
    persist: bool = True,
    recent_messages: list[dict[str, Any]] | None = None,
) -> RagAnswerResult:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question is empty")

    plant = _resolve_plant(db, plant_id)
    session = None
    can_persist = persist and current_user_id is not None

    if can_persist and session_id is not None:
        session = get_user_rag_session(db, user_id=current_user_id, session_id=session_id)
        if session is None:
            raise ValueError("Session not found")

    if can_persist and session is None:
        session = create_rag_session(
            db,
            user_id=current_user_id,
            title=_build_session_title(plant, normalized_question),
            current_plant_id=plant.get("id") if plant else None,
        )

    if session is not None and plant is not None:
        plant_changed = session.current_plant_id != plant.get("id")
        next_title = _build_session_title(plant, normalized_question) if plant_changed else session.title
        update_rag_session(
            db,
            session,
            current_plant_id=plant.get("id"),
            title=next_title or _build_session_title(plant, normalized_question),
            last_message_at=datetime.utcnow(),
        )
    elif session is not None:
        update_rag_session(db, session, last_message_at=datetime.utcnow())

    if session is not None:
        stored_history = list_rag_messages(db, session.id, limit=settings.RAG_RECENT_TURNS * 2)
        memory_messages = _normalize_memory_messages(stored_history)
    else:
        memory_messages = _normalize_memory_messages((recent_messages or [])[-settings.RAG_RECENT_TURNS * 2 :])

    prompt_messages = _build_prompt_messages(
        question=normalized_question,
        plant=plant,
        memory_messages=memory_messages,
    )

    provider = "bailian"
    try:
        answer = _call_bailian_chat_completion(prompt_messages)
    except Exception:
        provider = "local-fallback"
        answer = _fallback_answer(normalized_question, plant)

    if session is not None:
        create_rag_message(
            db,
            session_id=session.id,
            role="user",
            content=normalized_question,
            related_plant_id=plant.get("id") if plant else None,
            retrieval_context={
                "provider": provider,
                "plant_id": plant.get("id") if plant else None,
            },
        )
        create_rag_message(
            db,
            session_id=session.id,
            role="assistant",
            content=answer,
            related_plant_id=plant.get("id") if plant else None,
            retrieval_context={
                "provider": provider,
                "plant_id": plant.get("id") if plant else None,
            },
        )
        session_payload = rag_session_to_dict(session, include_messages=False)
        session_payload["messages"] = list_rag_messages(db, session.id, limit=settings.RAG_RECENT_TURNS * 2)
    else:
        session_payload = None

    if current_user_id is not None:
        try:
            create_rag_query(
                db,
                user_id=current_user_id,
                query_text=normalized_question,
                matched_doc_ids=[],
                retrieval_type="plant_species" if plant else "general",
                answer_text=answer,
            )
        except Exception:
            pass

    if session is None:
        base_recent_messages = _normalize_memory_messages(recent_messages or [])[-settings.RAG_RECENT_TURNS * 2 :]
        response_recent_messages = [
            {
                "id": index + 1,
                "session_id": 0,
                "role": item["role"],
                "content": item["content"],
                "related_plant_id": plant.get("id") if plant else None,
                "retrieval_context": {"provider": "client-memory"},
                "created_at": None,
            }
            for index, item in enumerate(base_recent_messages)
        ]
    else:
        response_recent_messages = list_rag_messages(db, session.id, limit=settings.RAG_RECENT_TURNS * 2)

    response_recent_messages.extend(
        [
            {
                "id": 0,
                "session_id": session.id if session is not None else 0,
                "role": "user",
                "content": normalized_question,
                "related_plant_id": plant.get("id") if plant else None,
                "retrieval_context": {"provider": provider},
                "created_at": None,
            },
            {
                "id": 0,
                "session_id": session.id if session is not None else 0,
                "role": "assistant",
                "content": answer,
                "related_plant_id": plant.get("id") if plant else None,
                "retrieval_context": {"provider": provider},
                "created_at": None,
            },
        ]
    )

    return RagAnswerResult(
        session=session_payload,
        answer=answer,
        provider=provider,
        plant=plant,
        retrieved_plant_context={
            "plant": plant,
            "memory_turns": len(memory_messages),
            "prompt_preview": prompt_messages[:3],
        },
        recent_messages=response_recent_messages[-settings.RAG_RECENT_TURNS * 2 :],
    )


def stream_answer_events(
    db: Session,
    *,
    question: str,
    plant_id: int | None = None,
    session_id: int | None = None,
    current_user_id: int | None = None,
    persist: bool = True,
    recent_messages: list[dict[str, Any]] | None = None,
) -> Iterator[dict[str, Any]]:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question is empty")

    plant = _resolve_plant(db, plant_id)
    session = None
    can_persist = persist and current_user_id is not None

    if can_persist and session_id is not None:
        session = get_user_rag_session(db, user_id=current_user_id, session_id=session_id)
        if session is None:
            raise ValueError("Session not found")

    if can_persist and session is None:
        session = create_rag_session(
            db,
            user_id=current_user_id,
            title=_build_session_title(plant, normalized_question),
            current_plant_id=plant.get("id") if plant else None,
        )

    if session is not None and plant is not None:
        plant_changed = session.current_plant_id != plant.get("id")
        next_title = _build_session_title(plant, normalized_question) if plant_changed else session.title
        update_rag_session(
            db,
            session,
            current_plant_id=plant.get("id"),
            title=next_title or _build_session_title(plant, normalized_question),
            last_message_at=datetime.utcnow(),
        )
    elif session is not None:
        update_rag_session(db, session, last_message_at=datetime.utcnow())

    if session is not None:
        stored_history = list_rag_messages(db, session.id, limit=settings.RAG_RECENT_TURNS * 2)
        memory_messages = _normalize_memory_messages(stored_history)
    else:
        memory_messages = _normalize_memory_messages((recent_messages or [])[-settings.RAG_RECENT_TURNS * 2 :])

    prompt_messages = _build_prompt_messages(
        question=normalized_question,
        plant=plant,
        memory_messages=memory_messages,
    )

    session_payload = rag_session_to_dict(session, include_messages=False) if session is not None else None
    yield {
        "type": "start",
        "session_id": session.id if session is not None else None,
        "title": session.title if session is not None else None,
        "plant": plant,
        "session": session_payload,
    }

    provider = "bailian"
    answer_parts: list[str] = []
    try:
        for chunk in _call_bailian_chat_completion_stream(prompt_messages):
            answer_parts.append(chunk)
            yield {"type": "delta", "content": chunk}
    except Exception:
        provider = "local-fallback"
        fallback_answer = _fallback_answer(normalized_question, plant)
        for chunk in _iter_text_chunks(fallback_answer):
            answer_parts.append(chunk)
            yield {"type": "delta", "content": chunk}

    answer = "".join(answer_parts)

    if session is not None:
        create_rag_message(
            db,
            session_id=session.id,
            role="user",
            content=normalized_question,
            related_plant_id=plant.get("id") if plant else None,
            retrieval_context={
                "provider": provider,
                "plant_id": plant.get("id") if plant else None,
            },
        )
        create_rag_message(
            db,
            session_id=session.id,
            role="assistant",
            content=answer,
            related_plant_id=plant.get("id") if plant else None,
            retrieval_context={
                "provider": provider,
                "plant_id": plant.get("id") if plant else None,
            },
        )
        session_payload = rag_session_to_dict(session, include_messages=False)
        session_payload["messages"] = list_rag_messages(db, session.id, limit=settings.RAG_RECENT_TURNS * 2)
        response_recent_messages = list_rag_messages(db, session.id, limit=settings.RAG_RECENT_TURNS * 2)
    else:
        base_recent_messages = _normalize_memory_messages(recent_messages or [])[-settings.RAG_RECENT_TURNS * 2 :]
        response_recent_messages = [
            {
                "id": index + 1,
                "session_id": 0,
                "role": item["role"],
                "content": item["content"],
                "related_plant_id": plant.get("id") if plant else None,
                "retrieval_context": {"provider": "client-memory"},
                "created_at": None,
            }
            for index, item in enumerate(base_recent_messages)
        ]
        response_recent_messages.extend(
            [
                {
                    "id": 0,
                    "session_id": 0,
                    "role": "user",
                    "content": normalized_question,
                    "related_plant_id": plant.get("id") if plant else None,
                    "retrieval_context": {"provider": provider},
                    "created_at": None,
                },
                {
                    "id": 0,
                    "session_id": 0,
                    "role": "assistant",
                    "content": answer,
                    "related_plant_id": plant.get("id") if plant else None,
                    "retrieval_context": {"provider": provider},
                    "created_at": None,
                },
            ]
        )
        session_payload = None

    if current_user_id is not None:
        try:
            create_rag_query(
                db,
                user_id=current_user_id,
                query_text=normalized_question,
                matched_doc_ids=[],
                retrieval_type="plant_species" if plant else "general",
                answer_text=answer,
            )
        except Exception:
            pass

    yield {
        "type": "done",
        "session_id": session.id if session is not None else None,
        "title": session.title if session is not None else None,
        "answer": answer,
        "provider": provider,
        "plant": plant,
        "session": session_payload,
        "recent_messages": response_recent_messages[-settings.RAG_RECENT_TURNS * 2 :],
    }
