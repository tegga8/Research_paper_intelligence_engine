#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x backend/.venv/bin/uvicorn ]]; then
  echo "Backend environment missing. Run ./scripts/setup-local.sh first."
  exit 1
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "Frontend dependencies missing. Run ./scripts/setup-local.sh first."
  exit 1
fi

cleanup() {
  jobs -p | xargs -r kill
}
trap cleanup EXIT

(
  cd backend
  source .venv/bin/activate
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &

(
  cd frontend
  NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev
) &

wait
