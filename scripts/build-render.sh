#!/usr/bin/env bash
set -euo pipefail

# Render (repo root):
#   Root Directory:  (empty — repository root, not backend)
#   Build Command:   bash scripts/build-render.sh
#   Start Command:   cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ensure_npm() {
  if command -v npm >/dev/null 2>&1; then
    return
  fi

  local node_dir="$ROOT/.node"
  local version="v22.16.0"
  mkdir -p "$node_dir"
  curl -fsSL "https://nodejs.org/dist/${version}/node-${version}-linux-x64.tar.xz" \
    | tar -xJ -C "$node_dir" --strip-components=1
  export PATH="$node_dir/bin:$PATH"
}

ensure_npm

cd "$ROOT/frontend"
npm ci
npm run build

cd "$ROOT/backend"
pip install -r requirements.txt
