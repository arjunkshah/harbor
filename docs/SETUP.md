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

## Live stack

1. Copy environment file:

```bash
cp .env.example .env
```

2. Add API keys — see [CREDITS.md](CREDITS.md) for BuilderShip sponsor credits.

3. Connect Composio apps:

```bash
source .venv/bin/activate
harbor connect github
harbor connect slack
harbor connect linear
harbor connect gmail
```

4. Set workflow targets in `.env`:

```bash
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo
SLACK_CHANNEL_ID=C01234567
LINEAR_TEAM_ID=your-team-uuid
```

5. Verify:

```bash
harbor doctor
harbor brief
```

## Web UI + API server

```bash
harbor serve
# → http://localhost:8787  (landing page)
# → http://localhost:8787/health
# → http://localhost:8787/docs  (OpenAPI)
```

## OpenClaw

```bash
openclaw plugins install @composio/openclaw-plugin
harbor serve
# Point OpenClaw webhook → http://127.0.0.1:8787/openclaw/chat
```

See `openclaw/SKILL.md`.

## Nebius deploy

```bash
openclaw skills install nebius
./deploy/nebius/deploy.sh
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No memory checkpoint` | `python scripts/train_memory_checkpoint.py --fast` |
| Composio auth errors | `harbor connect <toolkit>` and complete OAuth |
| Empty brief | Check `.env` keys; run `harbor doctor` |
| Demo vs live | `HARBOR_DEMO=0` in `.env` for submission |
