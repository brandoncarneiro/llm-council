"""File-backed conversation storage with strict ID handling."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from .config import DATA_DIR


class InvalidConversationIdError(ValueError):
    """Raised when a conversation ID cannot be safely mapped to one file."""


def _storage_dir() -> Path:
    return Path(DATA_DIR).expanduser()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_data_dir() -> None:
    _storage_dir().mkdir(parents=True, exist_ok=True)


def normalize_conversation_id(conversation_id: str) -> str:
    try:
        return str(UUID(str(conversation_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise InvalidConversationIdError("Invalid conversation ID") from exc


def get_conversation_path(conversation_id: str) -> Path:
    safe_id = normalize_conversation_id(conversation_id)
    base = _storage_dir().resolve()
    path = (base / f"{safe_id}.json").resolve()
    if path.parent != base:
        raise InvalidConversationIdError("Invalid conversation path")
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_data_dir()
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.stem}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
        temp_path = Path(handle.name)

    temp_path.replace(path)


def create_conversation(conversation_id: str) -> dict[str, Any]:
    safe_id = normalize_conversation_id(conversation_id)
    conversation = {
        "id": safe_id,
        "created_at": _now_iso(),
        "title": "New Conversation",
        "messages": [],
    }
    _write_json(get_conversation_path(safe_id), conversation)
    return conversation


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    path = get_conversation_path(conversation_id)
    if not path.exists() or path.is_symlink():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_conversation(conversation: dict[str, Any]) -> None:
    safe_id = normalize_conversation_id(str(conversation.get("id", "")))
    conversation["id"] = safe_id
    _write_json(get_conversation_path(safe_id), conversation)


def list_conversations() -> list[dict[str, Any]]:
    ensure_data_dir()
    summaries: list[dict[str, Any]] = []

    for path in sorted(_storage_dir().glob("*.json")):
        if path.is_symlink():
            continue
        try:
            normalize_conversation_id(path.stem)
            with path.open("r", encoding="utf-8") as handle:
                conversation = json.load(handle)
        except (InvalidConversationIdError, OSError, json.JSONDecodeError):
            continue

        summaries.append(
            {
                "id": conversation["id"],
                "created_at": conversation["created_at"],
                "title": conversation.get("title") or "New Conversation",
                "message_count": len(conversation.get("messages", [])),
            }
        )

    return sorted(summaries, key=lambda item: item["created_at"], reverse=True)


def _append_message(conversation_id: str, message: dict[str, Any]) -> None:
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation not found: {conversation_id}")
    conversation.setdefault("messages", []).append(message)
    save_conversation(conversation)


def add_user_message(conversation_id: str, content: str) -> None:
    _append_message(conversation_id, {"role": "user", "content": content})


def add_assistant_message(
    conversation_id: str,
    stage1: list[dict[str, Any]],
    stage2: list[dict[str, Any]],
    stage3: dict[str, Any],
) -> None:
    _append_message(
        conversation_id,
        {"role": "assistant", "stage1": stage1, "stage2": stage2, "stage3": stage3},
    )


def update_conversation_title(conversation_id: str, title: str) -> None:
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation not found: {conversation_id}")
    conversation["title"] = title.strip()[:80] or "New Conversation"
    save_conversation(conversation)


def delete_conversation(conversation_id: str) -> bool:
    path = get_conversation_path(conversation_id)
    if not path.exists() or path.is_symlink():
        return False
    path.unlink()
    return True
