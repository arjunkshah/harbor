# Harbor

**Autonomous builder workspace for vibe coders** — ideate, queue Codex/Claude Code, connect your stack, ship.

📦 **https://github.com/arjunkshah/harbor**

---

## For users (start here)

**Already in this folder?** Do NOT `git clone` into `./harbor` — that name is the Python package.

```bash
cd /path/to/buildersshipbycursor   # repo root (pyproject.toml here)
chmod +x bootstrap.sh && ./bootstrap.sh
source .venv/bin/activate
harbor setup
harbor dashboard
```

Fresh clone elsewhere:

```bash
git clone https://github.com/arjunkshah/harbor.git my-harbor && cd my-harbor
./bootstrap.sh --setup
```

Or:

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e .
harbor setup
```

### Web

**Project site (GitHub Pages)** — what Harbor is, how it works, docs, install:  
https://arjunkshah.github.io/harbor/

**Local dashboard** — integrations, run history, live briefs (not on GitHub Pages):

```bash
harbor serve
# → http://127.0.0.1:8787/dashboard
```

---

## Commands

| Command | Description |
|---------|-------------|
| **`harbor setup`** | Interactive wizard — API keys → `.env` → checkpoint → Composio OAuth → doctor |
| `harbor integrations list` | See enabled vs OAuth-connected integrations |
| `harbor integrations set github,gmail,notion` | Choose which Composio apps Harbor uses |
| `harbor dashboard` | Open local workspace (starts server) |
| `harbor serve` | Local server — dashboard + API (not GitHub Pages) |
| `harbor run "…"` | General builder agent task |
| `harbor run "…" --plan` | Plan only → `.harbor/plans.json` |
| **`harbor build ideate "…"`** | Refine idea → `docs/harbor/ideation.md` |
| **`harbor build approve`** | PRD + feature docs + queue Codex/Claude |
| **`harbor build queue "…"`** | Queue custom coding prompt |
| **`harbor build status --watch`** | Monitor queue + alerts |
| **`harbor sync all`** | Sync plans + PRD to Harbor Board + connected apps (GitHub, Notion, Slack, Gmail, …) |
| **`harbor sync status`** | Ecosystem sync registry |
| `harbor brief` | Morning brief workflow |
| `harbor incident "…"` | Incident commander |
| `harbor doctor --fix` | Migrate deprecated settings + verify stack |
| `harbor connect github --wait` | OAuth-link GitHub (waits until done) |
| `harbor connect-all` | Connect all enabled apps |
| `harbor demo` | No API keys required |

---

## API keys (BuilderShip credits)

See **[docs/CREDITS.md](docs/CREDITS.md)** — register at [ship.builders](https://ship.builders), then get keys from Nebius, Composio, Tavily.

`harbor setup` prompts for all keys and writes `.env` for you.

---

## Architecture

```
User → Dashboard / CLI
         → Harbor Board (kanban — primary planning surface)
         → Tavily (research)
         → Composio (GitHub · Gmail · Slack · Notion · …)
         → SuperCompress (memory)
         → Nebius (inference + tools)
         → Composio actions + Gmail sync (send by default)
         → .harbor/runs.json (history for dashboard)
```

---

## Docs

- [docs/SETUP.md](docs/SETUP.md)
- [docs/CREDITS.md](docs/CREDITS.md)
- [SUBMISSION.md](SUBMISSION.md)

## License

MIT
