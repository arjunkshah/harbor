---
name: harbor
description: Builder ops agent — morning briefs, incident response, cross-app automation via Composio + Tavily + Nebius with SuperCompress memory.
metadata:
  openclaw:
    emoji: "⚓"
    requires:
      bins: ["harbor", "python3"]
---

# Harbor Agent Skill

Harbor is your builder operations co-pilot for the BuilderShip stack.

## Capabilities

- **Morning Brief** — Tavily market intel + Composio GitHub/Linear/Gmail → SuperCompress → Nebius synthesis → Slack + Linear actions
- **Incident Commander** — Real-time Tavily search + cross-app status updates
- **Memory layer** — SuperCompress trims context before every Nebius inference turn

## Commands (via Harbor CLI or HTTP bridge)

```bash
harbor doctor          # verify full stack
harbor brief           # run morning brief workflow
harbor incident "..."  # incident commander
harbor serve           # OpenClaw webhook bridge on :8787
```

## OpenClaw integration

1. Install Harbor: `pip install -e .` in the harbor-agent repo
2. Start bridge: `harbor serve`
3. Point OpenClaw at `http://127.0.0.1:8787/openclaw/chat`

Or install Composio plugin for native tool access:

```bash
openclaw plugins install @composio/openclaw-plugin
```

## Environment

Copy `.env.example` → `.env` and set:

- `NEBIUS_API_KEY` — Token Factory inference
- `COMPOSIO_API_KEY` — GitHub, Slack, Linear, Gmail
- `TAVILY_API_KEY` — search + extract + research
- `GITHUB_OWNER`, `GITHUB_REPO`, `SLACK_CHANNEL_ID`, `LINEAR_TEAM_ID`

## Nebius deploy

```bash
openclaw skills install nebius
./deploy/nebius/deploy.sh
```

See `deploy/nebius/` for serverless Dockerfile and deploy script.
