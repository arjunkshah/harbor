# Harbor

**Autonomous builder ops for the [BuilderShip](https://ship.builders) stack.**

Harbor runs morning briefs and incident response across **Tavily**, **Composio**, **Nebius**, **OpenClaw**, and **SuperCompress**.

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
| `harbor integrations set github,linear` | Choose which Composio apps Harbor uses |
| `harbor dashboard` | Open local workspace (starts server) |
| `harbor serve` | Local server — dashboard + API (not GitHub Pages) |
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
