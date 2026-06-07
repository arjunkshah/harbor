#!/usr/bin/env bash
# Deploy Harbor Agent to Nebius Serverless (OpenClaw + Token Factory pattern)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "==> Building Harbor container..."
docker build -f deploy/Dockerfile -t harbor-agent:latest .

echo ""
echo "==> Nebius Serverless deploy"
echo "Requires: openclaw skills install nebius (or Nebius CLI configured)"
echo ""
echo "Manual steps:"
echo "  1. Push image to your registry accessible from Nebius"
echo "  2. Create serverless endpoint with env vars from .env.example"
echo "  3. Set NEBIUS_API_KEY, COMPOSIO_API_KEY, TAVILY_API_KEY"
echo ""
echo "OpenClaw one-liner (when nebius skill installed):"
echo "  openclaw skills install nebius"
echo "  # Then from OpenClaw chat: /nebius deploy harbor-agent:latest"
echo ""
echo "Local smoke test:"
echo "  docker run --rm -p 8787:8787 -e HARBOR_DEMO=1 harbor-agent:latest"
