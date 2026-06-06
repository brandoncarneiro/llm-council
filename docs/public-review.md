# Public Review Notes

LLM Council is public by design as a local, inspectable decision-support prototype. It should be reviewed as a working local app, not as a hosted production service.

## What A Reviewer Can Verify

- FastAPI backend orchestration for three-stage council runs.
- React/Vite frontend with streaming event handling.
- Local JSON conversation storage with UUID-only file access.
- Backend tests for ranking, storage, API behavior, and OpenRouter client behavior.
- Frontend lint, tests, and production build in CI.
- Dependency audits for Python and frontend packages.
- Secret-scan and public-tree hygiene checks in CI.

## Public Boundary

The repository should not contain `.env`, OpenRouter keys, local conversations, logs, screenshots, databases, or generated decision artifacts. The default posture is local development only.

## Production Boundary

Do not treat this repository as deploy-ready without adding authentication, authorization, rate limits, production CORS/host controls, durable storage, monitoring, and a deployment runbook.

## Quality Bar

The public surface should stay honest about:

- local-only runtime assumptions
- OpenRouter dependency
- model availability risk
- decision-support scope
- attribution to public inspiration without copying unlicensed implementation code
