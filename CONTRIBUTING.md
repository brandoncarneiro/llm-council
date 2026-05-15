# Contributing

LLM Council is a small local app. Keep contributions focused, tested, and honest
about what the project does today.

## Setup

```bash
uv sync --dev
cd frontend
npm install
cd ..
cp .env.example .env
```

Add an OpenRouter key to `.env` before running real model calls.

## Required Checks

Backend:

```bash
uv run ruff check .
uv run pytest
uv run python -m compileall backend tests
uv audit
uv run pip-audit
```

Frontend:

```bash
cd frontend
npm run lint
npm run test
npm run build
npm audit --audit-level=moderate
```

## Pull Request Rules

- Keep the change narrow.
- Add tests for behavior changes.
- Preserve the inspiration attribution in `README.md` and `NOTICE.md`.
- Do not add copied code from unlicensed projects.
- Do not commit `.env`, local conversation data, logs, screenshots, reports, or
  generated artifacts.
- Do not claim production readiness unless authentication, authorization, rate
  limits, durable storage, monitoring, and deployment controls are actually in
  the change.
