# BuilderShip submission — Harbor

**Repo:** https://github.com/arjunkshah/harbor  
**Web:** `harbor serve` → http://localhost:8787  
**Deadline:** June 12, 23:59 PT

## One-liner

Harbor is an autonomous builder-ops agent: **Tavily** research → **Composio** cross-app gather → **SuperCompress** memory → **Nebius** inference → **Composio** actions — runnable via CLI, web, or **OpenClaw**.

## Judge demo (copy-paste)

```bash
git clone https://github.com/arjunkshah/harbor.git && cd harbor
./scripts/install_and_demo.sh          # no keys — proves stack
cp .env.example .env                   # add sponsor keys for live run
harbor doctor && harbor brief
harbor serve                           # landing page + API
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
