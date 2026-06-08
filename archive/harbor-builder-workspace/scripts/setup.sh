#!/usr/bin/env bash
# Interactive setup — delegates to harbor setup
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -U pip -q
pip install -e . -q

exec harbor setup "$@"
