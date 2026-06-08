# BuilderShip sponsor credits & API keys

Harbor needs **three API keys** for the live stack. As a registered BuilderShip hacker, sponsors provide credits **from day one** through **June 12, 23:59 PT**.

## Where to get keys (BuilderShip)

| Sponsor | What you get | Where to get it |
|---------|--------------|-----------------|
| **Nebius** | Token Factory keys + GPU credits for inference & deploy | Register at [ship.builders](https://ship.builders) → sign up to hack. Docs: [tokenfactory.nebius.com](https://tokenfactory.nebius.com) → Create API key. Discord: [Nebius Discord](https://ship.builders) (linked from site) |
| **Composio** | API access for 250+ app toolkits (GitHub, Slack, Linear, Gmail) | [dashboard.composio.dev](https://dashboard.composio.dev) → API Keys. BuilderShip builders get access when registered. Discord: Composio Discord (from ship.builders) |
| **Tavily** | Search, extract, research API credits | [tavily.com](https://tavily.com) → API key. BuilderShip provides API access for the event. Community: Tavily Community (from ship.builders) |
| **OpenClaw** | Free runtime — no API key | [openclaw.ai](https://openclaw.ai) / docs — install locally. Optional gateway token for webhook bridge |

### BuilderShip registration (do this first)

1. **[Sign Up to Hack](https://ship.builders/#apply)** — name, email, what you're building
2. **[Luma ticket](https://luma.com/ship.builders)** — choose **Hacker** (requires approval)
3. Join sponsor Discords from [ship.builders → Developer Support](https://ship.builders) for office hours and credit questions

> **Note:** Exact credit amounts are distributed through the hackathon onboarding (Discord / registration email). The site states: *"Nebius Token Factory keys through June 12, Nebius GPU credits, Composio + Tavily API access — available from day one."*

## Keys Harbor uses in `.env`

```bash
NEBIUS_API_KEY=           # Token Factory → https://tokenfactory.nebius.com
COMPOSIO_API_KEY=           # → https://dashboard.composio.dev
TAVILY_API_KEY=             # → https://app.tavily.com

# Optional — target your apps for live brief
GITHUB_OWNER=
GITHUB_REPO=
SLACK_CHANNEL_ID=
LINEAR_TEAM_ID=
HARBOR_USER_ID=harbor-builder-001
```

**OpenClaw** does not need a cloud API key for local use. Set `OPENCLAW_GATEWAY_TOKEN` only if you wire the webhook bridge to a secured gateway.

## Connect OAuth apps (Composio)

After `COMPOSIO_API_KEY` is set:

```bash
harbor connect github
harbor connect slack
harbor connect linear
harbor connect gmail
```

Follow the OAuth links — Composio hosts auth; no manual token paste per app.

## Verify everything

```bash
cp .env.example .env   # fill keys
harbor doctor          # all green
harbor brief           # live morning brief
```

## Demo mode (no keys)

For video structure or CI:

```bash
HARBOR_DEMO=1 harbor demo
```

Uses fixture data — not for final submission demo (judges want live stack).
