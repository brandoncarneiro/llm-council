"""Small OpenRouter client used by the council runner."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL

LOGGER = logging.getLogger(__name__)

ChatMessage = Mapping[str, str]
ModelReply = dict[str, Any]


def _request_headers() -> dict[str, str] | None:
    if not OPENROUTER_API_KEY:
        LOGGER.warning("OPENROUTER_API_KEY is not configured")
        return None

    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/sommbc/llm-council",
        "X-Title": "LLM Council",
    }


def _extract_message(payload: Mapping[str, Any]) -> ModelReply | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        return None

    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        return None

    return {
        "content": message.get("content") or "",
        "reasoning_details": message.get("reasoning_details"),
    }


async def query_model(
    model: str,
    messages: Sequence[ChatMessage],
    timeout: float = 120.0,
) -> ModelReply | None:
    """Return one model response, or None when the provider call fails."""
    headers = _request_headers()
    if headers is None:
        return None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json={"model": model, "messages": list(messages)},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        LOGGER.warning("OpenRouter request failed for %s: %s", model, exc)
        return None

    try:
        return _extract_message(response.json())
    except ValueError:
        LOGGER.warning("OpenRouter returned non-JSON content for %s", model)
        return None


async def query_models_parallel(
    models: Sequence[str],
    messages: Sequence[ChatMessage],
) -> dict[str, ModelReply | None]:
    """Query several models with the same messages while preserving model keys."""
    tasks = [query_model(model, messages) for model in models]
    replies = await asyncio.gather(*tasks)
    return dict(zip(models, replies, strict=True))


async def query_advisors_parallel(
    advisor_calls: Sequence[Mapping[str, Any]],
) -> dict[str, ModelReply | None]:
    """Query role-specific advisors in parallel."""
    tasks = [
        query_model(str(call["model"]), call["messages"])
        for call in advisor_calls
    ]
    replies = await asyncio.gather(*tasks)
    return {
        str(call["role"]): reply
        for call, reply in zip(advisor_calls, replies, strict=True)
    }
