# Harbor Builder Workspace — Archived Snapshot

**This folder is a self-contained archive of the full Harbor builder workspace project** (dashboard, board, build pipeline, Composio integrations, marketing site, tests, CI).

Move this entire folder out of the repo when starting fresh on the **SuperCompress Agent Memory Layer** product.

## What's inside

| Path | Description |
|------|-------------|
| `harbor/` | Python package — agent loop, memory, Composio, Nebius, Tavily, CLI, server |
| `local/` | Dashboard UI (`harbor serve` → `/dashboard`) |
| `web/` | GitHub Pages marketing site |
| `tests/` | 24 pytest tests |
| `openclaw/` | OpenClaw SKILL.md + gateway bridge |
| `docs/` | Setup, credits |
| `scripts/` | Install, train SuperCompress checkpoint |
| `examples/openclaw_agent_loop/` | **Runnable sponsor-stack demo** (what judges need) |

## Run from this folder

```bash
cd archive/harbor-builder-workspace
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/train_memory_checkpoint.py --fast

# Demo (no keys)
HARBOR_DEMO=1 python examples/openclaw_agent_loop/run.py

# Full workspace
HARBOR_DEMO=1 harbor doctor
HARBOR_DEMO=1 harbor serve
```

## Live stack

```bash
cp .env.example .env
harbor setup
harbor connect github --wait
python examples/openclaw_agent_loop/run.py --live
```

## Git history

Commits through `c0be2d6` on `arjunkshah/harbor` — also on GitHub.

## Fresh project direction (Tier A)

Focus: **SuperCompress as the Agent Memory Layer**

- One reproducible loop: Tavily → Composio → SuperCompress → Nebius
- OpenClaw as runtime hook, not the product
- `examples/openclaw_agent_loop/run.py` is the qualification artifact
