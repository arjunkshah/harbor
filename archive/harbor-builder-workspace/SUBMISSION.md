# BuilderShip submission checklist

**Repo:** https://github.com/arjunkshah/harbor  
**Event:** [BuilderShip](https://ship.builders) · Deadline **June 12, 23:59 PT**

## Before you submit

- [ ] Registered at [ship.builders](https://ship.builders/#apply)
- [ ] Luma **Hacker** ticket at [luma.com/ship.builders](https://luma.com/ship.builders)
- [ ] `.env` filled with live keys (see [docs/CREDITS.md](docs/CREDITS.md))
- [ ] `harbor doctor` — all components green (live mode)
- [ ] `harbor brief` — end-to-end with real Slack/Linear actions
- [ ] Public GitHub repo pushed
- [ ] README + docs accurate

## Application post (rolling selection)

Post on **X** or **LinkedIn** with:

```
Built Harbor — autonomous builder ops across the full BuilderShip stack.

Tavily intel → Composio GitHub/Slack/Linear/Gmail → SuperCompress memory → Nebius inference → actions back to your apps.

Agent loops die at turn 4. Harbor compresses context before every inference call.

harbor brief — one command.

https://github.com/arjunkshah/harbor
```

**Tags (required):** `@ship_builders @nebiusai @composio @tavilyai @openclaw`

## Video (60–90 sec)

1. Landing page: https://github.com/arjunkshah/harbor (or `harbor serve` locally)
2. `harbor doctor` — all green
3. `harbor brief` — show turn log: Tavily → Composio → SuperCompress **KV savings %** → Nebius → Slack action
4. One-line pitch: *"Memory + ops layer for agent builders"*

## GitHub submission (June 12)

- Public repo URL in post
- AI judges read the repo continuously
- CI green (GitHub Actions)

## Pitch (90 sec on boat)

1. **Problem:** Agent loops forget context by turn 4
2. **Solution:** Harbor — gather (Tavily + Composio) → compress (SuperCompress) → think (Nebius) → act (Composio)
3. **Demo:** `harbor brief` live
4. **Why now:** Every builder runs multi-app agents; nobody owns the memory layer

## Rubric self-check

| Axis | Harbor evidence |
|------|-----------------|
| Working demo | `harbor demo`, `harbor brief`, CI |
| Integration depth | 6 Tavily surfaces, 4 Composio toolkits, Nebius tool loop, OpenClaw skill |
| Usefulness | Morning brief + incident commander |
| Code quality | Tests, docs, Dockerfile, typed Python |
| Pitch | Video + this checklist |
