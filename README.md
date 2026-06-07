# Harbor

**Autonomous builder ops for the [BuilderShip](https://ship.builders) stack.**

Harbor runs morning briefs and incident response across **Tavily**, **Composio**, **Nebius**, **OpenClaw**, and **SuperCompress**.

📦 **https://github.com/arjunkshah/harbor**

---

## For users (start here)

```bash
git clone https://github.com/arjunkshah/harbor.git && cd harbor
pip install -e .
harbor setup          # ← interactive API keys, .env, OAuth, doctor
harbor dashboard      # ← pretty UI for your runs
```

Or one-shot install + demo:

```bash
./scripts/install_and_demo.sh
harbor setup
```

### Web app

| URL | What |
|-----|------|
| `/` | Marketing landing |
| `/docs` | Setup & integration docs |
| `/dashboard` | Your runs, health, trigger briefs |
| `/api/reference` | OpenAPI |

```bash
harbor serve
# http://localhost:8787
```

---

## Commands

| Command | Description |
|---------|-------------|
| **`harbor setup`** | Interactive wizard — API keys → `.env` → checkpoint → Composio OAuth → doctor |
| `harbor dashboard` | Open dashboard (starts server) |
| `harbor serve` | Web + docs + dashboard + API |
| `harbor brief` | Morning brief workflow |
| `harbor incident "…"` | Incident commander |
| `harbor doctor` | Verify integrations |
| `harbor demo` | No API keys required |

---

## API keys (BuilderShip credits)

See **[docs/CREDITS.md](docs/CREDITS.md)** — register at [ship.builders](https://ship.builders), then get keys from Nebius, Composio, Tavily.

`harbor setup` prompts for all keys and writes `.env` for you.

---

## Architecture

```
User → Dashboard / CLI
         → Tavily (research)
         → Composio (GitHub · Slack · Linear · Gmail)
         → SuperCompress (memory)
         → Nebius (inference + tools)
         → Composio (Slack · Linear actions)
         → .harbor/runs.json (history for dashboard)
```

---

## Docs

- [docs/SETUP.md](docs/SETUP.md)
- [docs/CREDITS.md](docs/CREDITS.md)
- [SUBMISSION.md](SUBMISSION.md)

## License

MIT
