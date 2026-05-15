# Architecture

LLM Council is intentionally small: a local FastAPI API, a React frontend, and
JSON files for conversation storage.

## Runtime Flow

1. The frontend creates or selects a conversation through the backend.
2. A user sends one question.
3. Stage 1 calls each configured advisor model independently.
4. Stage 2 builds an anonymized prompt using `Response A`, `Response B`, etc.
5. Each configured model ranks the anonymous answers.
6. The backend parses ranking labels and computes average rank by model.
7. Stage 3 asks the Chairman model for one final synthesis.
8. The assistant message is written to local JSON storage.

## Backend Modules

- `backend/config.py`: environment-backed settings, advisor roles, model IDs.
- `backend/openrouter.py`: minimal async client for OpenRouter chat completions.
- `backend/council.py`: orchestration, prompt builders, parser, aggregation.
- `backend/storage.py`: UUID-only local JSON storage with atomic writes.
- `backend/main.py`: FastAPI app, REST routes, and Server-Sent Events streaming.

## Storage Contract

Conversation IDs must be UUIDs. Each conversation maps to exactly one JSON file
under `LLM_COUNCIL_DATA_DIR`.

The storage layer rejects traversal-like IDs, absolute paths, encoded path
fragments, non-UUID names, and symlinked conversation files.

## Frontend Contract

The frontend is a local operator interface. It expects:

- `GET /api/conversations`
- `POST /api/conversations`
- `GET /api/conversations/{id}`
- `DELETE /api/conversations/{id}`
- `POST /api/conversations/{id}/message/stream`

The streaming route emits JSON Server-Sent Events with a `type` field. The
frontend does not rely on raw HTML rendering; model Markdown is rendered through
React components.

## Production Notes

This app is not production-ready as-is. Public deployment needs authentication,
authorization, rate limiting, request logging, durable storage, production CORS
and host checks, monitoring, and a policy for model cost controls.
