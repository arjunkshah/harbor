# SuperCompress Agent Memory Layer

**Fresh start.** The previous Harbor builder workspace lives in:

```
archive/harbor-builder-workspace/
```

Move that folder out when you're ready. Everything from the old project (dashboard, board, build pipeline, tests, site) is self-contained there.

---

## What this repo is now

**Tier A — SuperCompress as the agent memory layer**

Agent loops break at turn 4 when Tavily + Composio inflate context. SuperCompress compresses before each model call.

```
Tavily (gather) → Composio GitHub (act) → SuperCompress (memory) → Nebius (inference)
```

Judges need **runnable code**, not architecture prose.

---

## Run the sponsor-stack demo

```bash
cd archive/harbor-builder-workspace
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/train_memory_checkpoint.py --fast

# No API keys
HARBOR_DEMO=1 python examples/openclaw_agent_loop/run.py

# Live (after .env + OAuth)
python examples/openclaw_agent_loop/run.py --live
```

See [archive/harbor-builder-workspace/examples/openclaw_agent_loop/README.md](archive/harbor-builder-workspace/examples/openclaw_agent_loop/README.md).

---

## Archive contents

| Item | Path |
|------|------|
| Full Harbor codebase | `archive/harbor-builder-workspace/harbor/` |
| Dashboard + site | `archive/harbor-builder-workspace/local/`, `web/` |
| Tests + CI | `archive/harbor-builder-workspace/tests/`, `.github/` |
| OpenClaw bridge | `archive/harbor-builder-workspace/openclaw/` |
| Agent loop demo | `archive/harbor-builder-workspace/examples/openclaw_agent_loop/` |

Read [archive/harbor-builder-workspace/ARCHIVE_README.md](archive/harbor-builder-workspace/ARCHIVE_README.md).

---

## Next steps (fresh project)

1. `mv archive/harbor-builder-workspace ~/harbor-archive` (or wherever)
2. Rebuild root around `examples/openclaw_agent_loop` + minimal `harbor/memory`
3. Record demo: show KV savings at turn 4 vs FIFO
4. OpenClaw hook via `/openclaw/chat` (in archive server)

GitHub history for the old work: [github.com/arjunkshah/harbor](https://github.com/arjunkshah/harbor)
