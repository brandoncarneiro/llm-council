#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [[ -n "${BACKEND_PID}" ]]; then kill "${BACKEND_PID}" 2>/dev/null || true; fi
  if [[ -n "${FRONTEND_PID}" ]]; then kill "${FRONTEND_PID}" 2>/dev/null || true; fi
}

trap cleanup EXIT INT TERM

echo "Starting LLM Council"
echo "Backend:  http://localhost:8001"
echo "Frontend: http://localhost:5173"
echo

cd "${ROOT_DIR}"
uv run python -m backend.main &
BACKEND_PID=$!

cd "${ROOT_DIR}/frontend"
npm run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!

wait
