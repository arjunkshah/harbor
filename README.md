# Harbor

**Autonomous builder ops for the [BuilderShip](https://ship.builders) stack.**

Harbor runs morning briefs and incident response across **Tavily**, **Composio**, **Nebius Token Factory**, **OpenClaw**, and **SuperCompress** — the memory layer that keeps agent loops from forgetting at turn 4.

🌐 **Landing page:** run `harbor serve` → [localhost:8787](http://localhost:8787)  
📦 **Repo:** [github.com/arjunkshah/harbor](https://github.com/arjunkshah/harbor)

---

## What it does

| Command | Description |
|---------|-------------|
| `harbor brief` | Tavily intel + Composio gather → SuperCompress → Nebius → Slack + Linear |
| `harbor incident "…"` | Real-time search + cross-app incident response |
| `harbor doctor` | Verify all integrations |
| `harbor serve` | Web UI + REST API + OpenClaw webhook |
| `harbor demo` | Full demo with fixtures (no API keys) |

## Quick start

```bash
git clone https://github.com/arjunkshah/harbor.git && cd harbor
chmod +x scripts/install_and_demo.sh && ./scripts/install_and_demo.sh
```

Live stack:

```bash
cp .env.example .env   # see docs/CREDITS.md for BuilderShip sponsor keys
harbor connect github && harbor connect slack
harbor doctor && harbor brief
```

Full setup → **[docs/SETUP.md](docs/SETUP.md)**  
API keys & free credits → **[docs/CREDITS.md](docs/CREDITS.md)**  
Submission checklist → **[SUBMISSION.md](SUBMISSION.md)**

## Architecture

```
harbor brief
    │
    ├─ Tavily ─────── search, extract, company intel, social pulse
    ├─ Composio ───── GitHub · Linear · Gmail (read)
    ├─ SuperCompress ─ compress context (~35% token budget)
    ├─ Nebius ─────── Token Factory inference + tool calling
    └─ Composio ───── Slack post · Linear tickets (write)
```

## BuilderShip integration map

| Sponsor | Harbor usage |
|---------|--------------|
| **Tavily** | 6 surfaces: search, multi-search, extract, Q&A, company intel, social |
| **Composio** | Session + 4 toolkits, gather + execute in agent loop, MCP URL |
| **Nebius** | Chat completions every turn with tool calling |
| **OpenClaw** | SKILL.md, webhook `/openclaw/chat`, cron, Composio plugin docs |
| **SuperCompress** | `compress_for_turn()` before each Nebius call |

## Web UI

```bash
harbor serve
# http://localhost:8787 — landing page
# http://localhost:8787/docs — OpenAPI
# http://localhost:8787/health — stack status
```

## Development

```bash
pip install -e ".[dev]"
python scripts/train_memory_checkpoint.py --fast
HARBOR_DEMO=1 pytest -q
```

## Submission

Built for [BuilderShip](https://ship.builders) · Deadline **June 12, 23:59 PT**

Post template & video checklist → **[SUBMISSION.md](SUBMISSION.md)**

Tag: `@ship_builders @nebiusai @composio @tavilyai @openclaw`

## License

MIT
