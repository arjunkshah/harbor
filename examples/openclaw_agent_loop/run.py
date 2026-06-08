#!/usr/bin/env python3
"""
OpenClaw Agent Loop — Tavily → Composio GitHub → SuperCompress → Nebius

Runnable BuilderShip demo. See README.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _banner(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def run_loop(*, task: str, live: bool) -> int:
    if live:
        os.environ.pop("HARBOR_DEMO", None)
    else:
        os.environ["HARBOR_DEMO"] = "1"

    from harbor.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    from harbor.tavily import get_tavily
    from harbor.composio import get_composio
    from supercompress import compress_for_turn
    from harbor.agent.loop import HarborAgent

    mode = "LIVE" if not settings.demo_mode else "DEMO"
    _banner(f"OpenClaw Agent Loop ({mode})")
    print(f"Task: {task}\n")

    _banner("1 · Tavily — live context")
    tavily = get_tavily(settings)
    research = tavily.search_and_answer(f"{task} — AI builder tools 2026")
    tavily_block = research.to_context_block()
    print(tavily_block[:1200] + ("…" if len(tavily_block) > 1200 else ""))

    _banner("2 · Composio — GitHub snapshot")
    composio = get_composio(settings)
    github = composio.gather_github()
    gh_block = github.to_context_block()
    print(gh_block[:1200] + ("…" if len(gh_block) > 1200 else ""))

    _banner("3 · SuperCompress — memory before inference")
    context_blocks = [tavily_block, gh_block]
    compressed, mem = compress_for_turn(context_blocks, task, budget_ratio=settings.harbor_memory_budget)
    print(f"  Policy: {mem.policy_name}")
    print(f"  Tokens: {mem.original_tokens} → {mem.kept_tokens}")
    print(f"  KV savings: {mem.kv_savings_pct:.1f}%")

    _banner("4 · Nebius + Composio — agent loop")
    agent = HarborAgent(settings)
    result = agent.run_with_tools(
        system_prompt="You are Harbor's agent memory demo. Use Composio when helpful. Cite KV savings.",
        user_prompt=task,
        context_blocks=context_blocks,
        workflow="openclaw_agent_loop",
    )
    for t in result.turns:
        print(f"    [{t.phase}] {t.detail}")
    if result.actions_taken:
        print(f"\n  Actions ({len(result.actions_taken)}):")
        for a in result.actions_taken:
            print(f"    {'✓' if a.get('success') else '✗'} {a.get('tool')}")

    _banner("5 · Response")
    print(result.summary or "(no summary)")
    print(f"\n  KV savings: {result.memory_savings_pct:.1f}%")
    print("  Stack: Tavily → Composio → SuperCompress → Nebius\n")
    return 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--task", default="Triage my open GitHub PRs and suggest what to ship")
    p.add_argument("--live", action="store_true")
    args = p.parse_args()
    raise SystemExit(run_loop(task=args.task, live=args.live))


if __name__ == "__main__":
    main()
