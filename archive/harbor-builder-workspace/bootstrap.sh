#!/usr/bin/env bash
# One command to install Harbor from THIS folder (do not git clone into ./harbor)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> Harbor bootstrap (repo root: $ROOT)"
echo ""

if [[ ! -f pyproject.toml ]]; then
  echo "Error: run this from the harbor repo root (where pyproject.toml lives)."
  exit 1
fi

if [[ -d harbor/.git ]]; then
  echo "Error: ./harbor looks like a nested git clone and conflicts with the Python package."
  echo "  rm -rf harbor/.git   # only if you accidentally cloned inside harbor/"
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing Harbor..."
python3 -m pip install -U pip -q
python3 -m pip install -e ".[dev]" -q

if [[ ! -f checkpoints/default.pt ]]; then
  echo "Training memory checkpoint (~30s)..."
  python3 scripts/train_memory_checkpoint.py --fast
fi

echo ""
echo "✓ Installed. Commands (always activate venv first):"
echo "  source .venv/bin/activate"
echo "  harbor setup"
echo "  harbor dashboard"
echo ""

if [[ "${1:-}" == "--setup" ]]; then
  exec harbor setup "${@:2}"
fi

echo "Run:  source .venv/bin/activate && harbor setup"
