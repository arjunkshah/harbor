# Harbor × SuperCompress — Product Lock

**Harbor** is the demo harness. **SuperCompress** is the product.

Canonical spec (features, user flow, sponsors, winning strategy):  
**https://github.com/arjunkshah/supercompress/blob/main/PRODUCT.md**

## Quick reference

| Repo | Purpose |
|------|---------|
| [arjunkshah/supercompress](https://github.com/arjunkshah/supercompress) | Agent memory layer — `compress_for_turn()` |
| [arjunkshah/harbor](https://github.com/arjunkshah/harbor) | Runnable loop + dashboard + OpenClaw bridge |

## Loop (locked)

```
User → Tavily → Composio → SuperCompress → Nebius → Composio actions
```

## Judge demo

```bash
HARBOR_DEMO=1 python examples/openclaw_agent_loop/run.py
```

## Dependency

```toml
supercompress @ git+https://github.com/arjunkshah/supercompress.git
```

Harbor imports memory via `harbor.memory` (re-exports `supercompress`).
