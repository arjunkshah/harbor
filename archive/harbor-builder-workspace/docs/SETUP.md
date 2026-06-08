# Setup guide

## Requirements

- Python 3.10+
- Git

## Install

```bash
git clone https://github.com/arjunkshah/harbor.git
cd harbor
chmod +x scripts/install_and_demo.sh
./scripts/install_and_demo.sh
```

This creates a venv, installs Harbor, trains the SuperCompress checkpoint (~30s), and runs demo mode.

## Live stack (for demo video)

1. Copy environment file:

```bash
cp .env.example .env
```

2. Add API keys — see [CREDITS.md](CREDITS.md) for BuilderShip sponsor credits.

3. Migrate deprecated settings and verify:

```bash
harbor doctor --fix
harbor doctor
```

Default Nebius model is **`moonshotai/Kimi-K2.5`** (Kimi K2 Instruct builds were deprecated).

4. Connect Composio apps (OAuth in browser):

```bash
harbor connect github --wait
harbor connect gmail --wait
# or connect every enabled app:
harbor connect-all
```

5. Optional workflow targets in `.env`:

```bash
GITHUB_OWNER=your-org      # blank = whole GitHub account
GITHUB_REPO=your-repo      # optional narrow scope
SLACK_CHANNEL_ID=C01234567 # only if slack enabled
```

6. Verify all green:

```bash
harbor doctor
harbor brief
```

## Web UI + API server

```bash
harbor serve
# → http://localhost:8787/dashboard
# → http://localhost:8787/docs
```

## Quick commands

| Command | Purpose |
|---------|---------|
| `harbor setup` | Interactive wizard — keys, integrations, OAuth |
| `harbor doctor --fix` | Migrate deprecated `.env` values |
| `harbor connect github --wait` | OAuth + wait until linked |
| `harbor connect-all` | Connect all enabled apps |
| `harbor serve` | Dashboard + API |
| `harbor build ideate "…"` | Start build pipeline |
| `harbor sync all` | Push to Board + connected apps |

## Demo mode (no keys)

```bash
HARBOR_DEMO=1 harbor doctor
HARBOR_DEMO=1 harbor serve
```
