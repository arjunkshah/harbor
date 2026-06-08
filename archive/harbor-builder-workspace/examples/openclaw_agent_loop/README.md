# OpenClaw Agent Loop — Sponsor Stack Demo

**The reproducible end-to-end loop judges need:**

```
Tavily (gather) → Composio GitHub (act) → SuperCompress (memory) → Nebius (inference)
```

Agent loops break at turn 4 when Tavily + Composio inflate context. SuperCompress trims before every Nebius call — this script proves it in one run.

## Quick run (no API keys)

```bash
cd archive/harbor-builder-workspace   # or repo root before you move this folder out
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/train_memory_checkpoint.py --fast

HARBOR_DEMO=1 python examples/openclaw_agent_loop/run.py
```

## Live stack (BuilderShip keys)

```bash
cp .env.example .env
# Add NEBIUS_API_KEY, COMPOSIO_API_KEY, TAVILY_API_KEY
harbor doctor --fix
harbor connect github --wait

python examples/openclaw_agent_loop/run.py --live
```

## What it prints

1. **Tavily** — live search hits for your task
2. **Composio GitHub** — PRs, issues, commits from OAuth-linked account
3. **SuperCompress** — tokens before/after, KV savings %
4. **Nebius** — inference + tool calls (e.g. GitHub actions)
5. **Summary** — final agent response

## OpenClaw bridge

Point OpenClaw at Harbor's HTTP bridge (optional):

```bash
harbor serve
# POST http://127.0.0.1:8787/openclaw/chat  {"message": "..."}
```

See `openclaw/SKILL.md` in this archive.
