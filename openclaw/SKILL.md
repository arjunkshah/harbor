---
name: harbor
description: Builder workspace — projects, integration picks, agent prompts, and cross-app ops via Composio + Tavily + Nebius with SuperCompress memory.
metadata:
  openclaw:
    emoji: "⚓"
    requires:
      bins: ["harbor", "python3"]
---

# Harbor Agent Skill

Harbor is a **builder workspace** for vibe coders — not a single prompt. OpenClaw can call Harbor; Harbor owns memory, integrations, projects, and run history.

## What Harbor adds beyond OpenClaw

- **SuperCompress** — trims context before every Nebius turn (~35–65% KV savings)
- **Integration choice** — enable GitHub-only or add Linear/Gmail/Slack via `harbor integrations`
- **Projects** — active build context in the local dashboard
- **Prompt transparency** — view system + dynamic task prompts per workflow
- **Progress** — run history, turn logs, actions in `.harbor/`

## Commands

```bash
harbor setup              # API keys + pick integrations + OAuth
harbor integrations list  # see enabled vs connected
harbor integrations set github,linear,gmail
harbor doctor
harbor brief
harbor incident "..."
harbor serve              # local workspace dashboard :8787/dashboard
```

## OpenClaw bridge (optional)

Harbor is not OpenClaw. Use the bridge when you want OpenClaw to trigger Harbor workflows:

```bash
harbor serve
# POST http://127.0.0.1:8787/openclaw/chat
```

## Environment

See `.env.example`. Required: `NEBIUS_API_KEY`, `COMPOSIO_API_KEY`, `TAVILY_API_KEY`.  
Optional: `COMPOSIO_TOOLKITS=github,linear,gmail` (add `slack` only if needed).
