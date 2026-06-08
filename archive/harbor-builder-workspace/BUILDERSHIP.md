# BuilderShip submission — Harbor

**Repo:** https://github.com/arjunkshah/harbor  
**Web:** `harbor serve` → http://localhost:8787  
**Deadline:** June 12, 23:59 PT

## One-liner

Harbor is the **builder workspace** for vibe coders: projects + integration picks + agent prompts + progress — backed by a full **Tavily → Composio → SuperCompress → Nebius** loop. OpenClaw is one runtime bridge, not the product.

## Why not just OpenClaw?

| OpenClaw alone | Harbor |
|----------------|--------|
| Single chat / skill prompt | Multi-workflow agent (brief, incident) |
| No memory layer | SuperCompress before every inference turn |
| Manual tool wiring | Sponsor stack integrated out of the box |
| No run history | `.harbor/` runs, KV %, prompt snapshots |
| Pick-all integrations | Choose GitHub-only or add Linear/Gmail/Slack |

## Judge demo (copy-paste)

```bash
git clone https://github.com/arjunkshah/harbor.git && cd harbor
./scripts/install_and_demo.sh          # no keys — proves stack
cp .env.example .env                   # add sponsor keys for live run
harbor doctor && harbor brief
harbor serve                           # local workspace dashboard
harbor integrations list             # choose integrations
```

## Docs

- [SETUP.md](docs/SETUP.md) — install & configure
- [CREDITS.md](docs/CREDITS.md) — BuilderShip sponsor API keys
- [SUBMISSION.md](SUBMISSION.md) — post template & video checklist

## Rubric

| Axis | Evidence |
|------|----------|
| Working demo | `harbor demo`, `harbor brief`, web UI, CI |
| Integration depth | All 4 sponsors + SuperCompress in agent loop |
| Usefulness | Morning brief + incident commander |
| Code quality | Tests, typed Python, Dockerfile, docs |
| Pitch | "Memory + ops layer — agents that don't forget at turn 4" |
