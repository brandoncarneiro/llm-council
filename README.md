# LLM Council

[![CI](https://github.com/sommbc/llm-council/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/sommbc/llm-council/actions/workflows/ci.yml)

**A local, inspectable multi-model council for high-stakes founder and operator decisions.**

LLM Council sends one question to several role-specific LLM advisors through
OpenRouter, anonymizes their answers for peer review, ranks the responses, and
asks a Chairman model to synthesize the final answer.

It is for technical founders, operators, and AI engineers who want a concrete
multi-model workflow they can run locally, inspect, test, and adapt. It is not a
hosted SaaS product and it does not claim to make decisions for you.

```text
question -> independent advisors -> anonymous peer review -> aggregate ranking -> synthesis
```

## Why This Exists

Single-model answers can be smooth but narrow. They often inherit the user's
frame, underweight customer resistance, skip operational cost, or turn ambiguity
into confident prose.

LLM Council makes the disagreement explicit. The default council has five jobs:

- attack the premise
- reduce the decision to constraints
- represent customer/buyer reality
- look for asymmetric upside
- force execution order and kill criteria

The value is not "more agents." The value is an auditable decision process.

## What Works Today

- Local FastAPI backend
- React/Vite frontend
- OpenRouter model calls
- Five configurable advisor roles
- Anonymous Stage 2 peer review
- Aggregate ranking calculation
- Chairman synthesis
- Local JSON conversation storage
- Streaming progress events
- Backend and frontend tests
- CI for lint, tests, build, audits, and secret smoke checks

## Current Limitations

- No authentication or multi-user permissions
- No hosted deployment target
- No durable database backend
- No prompt/model editor in the UI
- No export flow for saved sessions
- No provider abstraction beyond OpenRouter
- Model availability depends on OpenRouter; the default model IDs were checked
  against OpenRouter's public model list on 2026-05-15

Do not expose the backend directly to the public internet without adding auth,
rate limiting, production CORS/host controls, logging, and durable storage.

## Quickstart

```bash
git clone https://github.com/sommbc/llm-council.git
cd llm-council
cp .env.example .env
```

Add your OpenRouter key to `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Install and run:

```bash
uv sync --dev
cd frontend
npm ci
cd ..
./start.sh
```

Open `http://localhost:5173`.

## Commands

| Task | Command |
|---|---|
| Install Python dependencies | `uv sync --dev` |
| Install frontend dependencies | `cd frontend && npm ci` |
| Run backend | `uv run python -m backend.main` |
| Run frontend | `cd frontend && npm run dev` |
| Run full local app | `./start.sh` |
| Backend tests | `uv run pytest` |
| Backend lint | `uv run ruff check .` |
| Python compile check | `uv run python -m compileall backend tests` |
| uv dependency audit | `uv audit` |
| Python dependency audit | `uv run pip-audit` |
| Frontend lint | `cd frontend && npm run lint` |
| Frontend tests | `cd frontend && npm run test` |
| Frontend build | `cd frontend && npm run build` |
| Frontend dependency audit | `cd frontend && npm audit --audit-level=moderate` |

## Successful Example

Input:

```text
Should we launch the product this month or cut scope first?
```

Expected behavior:

1. Stage 1 returns one answer per advisor role.
2. Stage 2 shows each model's anonymous peer review and extracted ranking.
3. The aggregate ranking lists which anonymized answer performed best.
4. Stage 3 returns one synthesized recommendation with tradeoffs and next steps.

See [examples/founder-decision-sample.md](examples/founder-decision-sample.md)
for a small synthetic sample.

## Architecture

```text
backend/
  config.py       advisor roles, model IDs, environment-backed settings
  openrouter.py   small async OpenRouter client
  council.py      orchestration, prompt builders, ranking parser
  storage.py      local JSON storage with UUID-only file access
  main.py         FastAPI routes and SSE streaming

frontend/
  src/api.js      fetch client and streaming reader
  src/sse.js      SSE frame parser
  src/components/ local app UI

docs/
  advisor-prompts.md
  architecture.md
```

Detailed notes: [docs/architecture.md](docs/architecture.md).

## Environment

| Variable | Required | Default | Notes |
|---|---:|---|---|
| `OPENROUTER_API_KEY` | Yes | none | Used only by the backend. Do not put this in frontend code. |
| `OPENROUTER_API_URL` | No | `https://openrouter.ai/api/v1/chat/completions` | Override for compatible gateways. |
| `LLM_COUNCIL_DATA_DIR` | No | `data/conversations` | Local JSON conversation directory. |
| `LLM_COUNCIL_TITLE_MODEL` | No | `google/gemini-2.5-flash` | Model used for conversation titles. |
| `LLM_COUNCIL_CHAIRMAN_MODEL` | No | `openai/gpt-5.5` | Model used for Stage 3 synthesis. |
| `VITE_API_BASE_URL` | No | `http://localhost:8001` | Public frontend config. Never put secrets in `VITE_*`. |

Advisor models and prompts live in `backend/config.py`.

## Security and Privacy

- `.env`, local data, logs, databases, screenshots, and generated artifacts are
  ignored by git.
- Conversation files are stored locally under `LLM_COUNCIL_DATA_DIR`.
- Conversation IDs are validated as UUIDs before any file path is constructed.
- The frontend uses normal React rendering and does not inject raw HTML.
- OpenRouter API keys stay server-side.
- The default CORS policy is local-development only.

Report vulnerabilities privately; see [SECURITY.md](SECURITY.md).

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| All advisors fail | Missing/invalid `OPENROUTER_API_KEY` or unavailable model IDs | Check `.env`, credits, and `backend/config.py` |
| Frontend cannot reach backend | Backend is not running or `VITE_API_BASE_URL` is wrong | Start `uv run python -m backend.main` |
| Empty conversation list after restart | Data dir changed or was deleted | Check `LLM_COUNCIL_DATA_DIR` |
| `npm audit` fails | Vulnerable frontend dependency | Run `npm audit fix`, then rerun tests/build |
| `pip-audit` fails | Vulnerable Python dependency | Upgrade safely with `uv add` / `uv lock`, then rerun tests |

## Roadmap

- UI for editing advisor roles and model IDs
- Export conversations to Markdown
- Database-backed storage option
- Provider abstraction beyond OpenRouter
- Better partial-failure reporting per model
- Optional local eval fixtures for prompt changes
- Deployment guide with authentication and rate limiting

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests should include tests for
behavior changes and must not include `.env`, local conversations, logs, or
generated artifacts.

## Attribution

This project is inspired by Andrej Karpathy's public
[`karpathy/llm-council`](https://github.com/karpathy/llm-council) experiment.
That upstream repository had no explicit license file or GitHub license metadata
when checked on 2026-05-15.

To avoid redistributing unlicensed upstream implementation code, this public
branch uses a rewritten implementation and keeps attribution at the concept and
inspiration level. See [NOTICE.md](NOTICE.md).

## License

MIT. See [LICENSE](LICENSE).
