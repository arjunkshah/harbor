#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

echo "==> Training SuperCompress checkpoint (fast)..."
python scripts/train_memory_checkpoint.py --fast

echo "==> Running harbor doctor (demo mode)..."
HARBOR_DEMO=1 harbor doctor

echo ""
echo "==> Running full demo workflow..."
HARBOR_DEMO=1 harbor demo

echo ""
echo "Done. Copy .env.example to .env, add API keys, then:"
echo "  harbor doctor"
echo "  harbor brief"
