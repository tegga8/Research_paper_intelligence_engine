#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON:-python3}"

echo "==> Creating Python virtual environment in backend/.venv"
$PYTHON_BIN -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

echo "==> Installing frontend dependencies"
cd frontend
npm install

echo "==> Local setup complete"
echo "Run: ./scripts/start-local.sh"
