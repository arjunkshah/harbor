# OpenClaw Agent Loop

Reproducible sponsor-stack demo for judges:

```
Tavily → Composio GitHub → SuperCompress → Nebius
```

SuperCompress package: https://github.com/arjunkshah/supercompress

## Run

```bash
pip install -e ".[dev]"
supercompress-train --fast   # or: python scripts/train_memory_checkpoint.py --fast

HARBOR_DEMO=1 python examples/openclaw_agent_loop/run.py
python examples/openclaw_agent_loop/run.py --live   # after harbor setup + OAuth
```

Full product spec: [supercompress PRODUCT.md](https://github.com/arjunkshah/supercompress/blob/main/PRODUCT.md)
