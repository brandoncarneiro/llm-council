# Security Policy

## Supported Versions

LLM Council is experimental local software. Security fixes are handled on the
default branch.

## Reporting a Vulnerability

Do not open a public issue for a suspected secret leak or exploitable
vulnerability.

Report privately by emailing Brandon Carneiro at `sommbc@gmail.com` with:

- A short description of the issue
- Steps to reproduce
- Impact and affected files/routes
- Any suggested fix, if known

## Security Notes

- Keep `OPENROUTER_API_KEY` only in local `.env` files or deployment secrets.
- Do not commit `data/`, `.env`, logs, database files, screenshots, or generated
  local artifacts.
- The backend is intended for local use. Do not expose it publicly without adding
  authentication, authorization, rate limiting, deployment-grade logging, and
  production CORS/host controls.
- Conversation IDs are UUID-backed and validated before file access.
- Model output is rendered as Markdown through React, not injected as raw HTML.
