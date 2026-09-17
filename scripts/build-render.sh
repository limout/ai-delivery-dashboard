#!/usr/bin/env bash
set -euo pipefail

# Future single-service Render build (repo root).
# Current Render Root Directory is still `backend` until settings are updated.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT/frontend"
npm ci
npm run build

cd "$ROOT/backend"
pip install -r requirements.txt
