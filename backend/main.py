"""FastAPI application for local LLM Council runs."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import storage
from .council import (
    calculate_aggregate_rankings,
    generate_conversation_title,
    run_full_council,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
)

LOCAL_ORIGINS = (
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
)


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class ConversationMetadata(BaseModel):
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    id: str
    created_at: str
    title: str
    messages: list[dict[str, Any]]


def create_app() -> FastAPI:
    app = FastAPI(title="LLM Council API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "llm-council"}

    @app.get("/api/conversations", response_model=list[ConversationMetadata])
    async def list_conversations() -> list[dict[str, Any]]:
        return storage.list_conversations()

    @app.post("/api/conversations", response_model=Conversation)
    async def create_conversation() -> dict[str, Any]:
        return storage.create_conversation(str(uuid4()))

    @app.get("/api/conversations/{conversation_id}", response_model=Conversation)
    async def get_conversation(conversation_id: str) -> dict[str, Any]:
        return _load_conversation(conversation_id)

    @app.delete("/api/conversations/{conversation_id}", status_code=204)
    async def delete_conversation(conversation_id: str) -> None:
        try:
            deleted = storage.delete_conversation(conversation_id)
        except storage.InvalidConversationIdError as exc:
            raise _invalid_id_error() from exc
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")

    @app.post("/api/conversations/{conversation_id}/message")
    async def send_message(conversation_id: str, request: SendMessageRequest) -> dict[str, Any]:
        conversation = _load_conversation(conversation_id)
        first_message = len(conversation.get("messages", [])) == 0

        storage.add_user_message(conversation_id, request.content)
        if first_message:
            title = await generate_conversation_title(request.content)
            storage.update_conversation_title(conversation_id, title)

        stage1, stage2, stage3, metadata = await run_full_council(request.content)
        storage.add_assistant_message(conversation_id, stage1, stage2, stage3)
        return {"stage1": stage1, "stage2": stage2, "stage3": stage3, "metadata": metadata}

    @app.post("/api/conversations/{conversation_id}/message/stream")
    async def stream_message(
        conversation_id: str,
        request: SendMessageRequest,
    ) -> StreamingResponse:
        conversation = _load_conversation(conversation_id)
        first_message = len(conversation.get("messages", [])) == 0

        return StreamingResponse(
            _stream_council_run(conversation_id, request.content, first_message),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    return app


def _invalid_id_error() -> HTTPException:
    return HTTPException(status_code=400, detail="Invalid conversation ID")


def _load_conversation(conversation_id: str) -> dict[str, Any]:
    try:
        conversation = storage.get_conversation(conversation_id)
    except storage.InvalidConversationIdError as exc:
        raise _invalid_id_error() from exc
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


async def _stream_council_run(
    conversation_id: str,
    content: str,
    first_message: bool,
) -> AsyncIterator[str]:
    title_task: asyncio.Task[str] | None = None

    try:
        storage.add_user_message(conversation_id, content)
        if first_message:
            title_task = asyncio.create_task(generate_conversation_title(content))

        yield _sse({"type": "stage1_start"})
        stage1 = await stage1_collect_responses(content)
        yield _sse({"type": "stage1_complete", "data": stage1})

        if not stage1:
            stage2: list[dict[str, Any]] = []
            stage3 = {
                "model": "none",
                "response": (
                    "No advisor models returned a response. "
                    "Check your OpenRouter key and model IDs."
                ),
            }
            metadata: dict[str, Any] = {}
        else:
            yield _sse({"type": "stage2_start"})
            stage2, label_to_model = await stage2_collect_rankings(content, stage1)
            model_to_role = {result["model"]: result["role"] for result in stage1}
            metadata = {
                "label_to_model": label_to_model,
                "label_to_role": {
                    label: model_to_role[model]
                    for label, model in label_to_model.items()
                    if model in model_to_role
                },
                "aggregate_rankings": calculate_aggregate_rankings(stage2, label_to_model),
            }
            yield _sse({"type": "stage2_complete", "data": stage2, "metadata": metadata})

            yield _sse({"type": "stage3_start"})
            stage3 = await stage3_synthesize_final(content, stage1, stage2)

        yield _sse({"type": "stage3_complete", "data": stage3})

        if title_task:
            title = await title_task
            storage.update_conversation_title(conversation_id, title)
            yield _sse({"type": "title_complete", "data": {"title": title}})

        storage.add_assistant_message(conversation_id, stage1, stage2, stage3)
        yield _sse({"type": "complete"})
    except Exception:
        yield _sse({"type": "error", "message": "Council run failed."})


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
