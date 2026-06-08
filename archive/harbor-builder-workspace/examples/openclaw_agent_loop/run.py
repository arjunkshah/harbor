#!/usr/bin/env python3
"""
OpenClaw Agent Loop — Tavily → Composio GitHub → SuperCompress → Nebius

Runnable proof of the BuilderShip sponsor stack + SuperCompress memory layer.
Demo mode works without API keys. Use --live with .env for real integrations.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from examples/ without global install
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
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
    from harbor.memory import compress_for_turn
    from harbor.nebius import get_nebius
    from harbor.agent.loop import HarborAgent

    mode = "LIVE" if not settings.demo_mode else "DEMO"
    _banner(f"OpenClaw Agent Loop ({mode})")
    print(f"Task: {task}\n")

    # --- 1. Tavily gather ---
    _banner("1 · Tavily — live context")
    tavily = get_tavily(settings)
    research = tavily.search_and_answer(f"{task} — AI builder tools 2026")
    tavily_block = research.to_context_block()
    print(tavily_block[:1200] + ("…" if len(tavily_block) > 1200 else ""))
    print(f"\n  hits: {len(research.hits)}")

    # --- 2. Composio GitHub gather ---
    _banner("2 · Composio — GitHub snapshot")
    composio = get_composio(settings)
    github = composio.gather_github()
    gh_block = github.to_context_block()
    print(gh_block[:1200] + ("…" if len(gh_block) > 1200 else ""))
    print(
        f"\n  PRs: {len(github.prs_needing_review)} | "
        f"issues: {len(github.open_issues)} | "
        f"commits: {len(github.recent_commits)}"
    )
    connected = composio.integration_status()
    linked = [k for k, v in connected.items() if v]
    print(f"  OAuth linked: {', '.join(linked) or 'none (demo fixtures)'}")

    # --- 3. SuperCompress ---
    _banner("3 · SuperCompress — memory before inference")
    context_blocks = [tavily_block, gh_block]
    compressed, mem = compress_for_turn(
        context_blocks,
        task,
        budget_ratio=settings.harbor_memory_budget,
    )
    print(f"  Policy: {mem.policy_name}")
    print(f"  Tokens: {mem.original_tokens} → {mem.kept_tokens}")
    print(f"  KV savings: {mem.kv_savings_pct:.1f}%")
    print(f"\n  Compressed preview:\n{compressed[:600]}…")

    # --- 4. Nebius inference loop (tools via Composio) ---
    _banner("4 · Nebius + Composio — agent loop")
    agent = HarborAgent(settings)
    result = agent.run_with_tools(
        system_prompt=(
            "You are Harbor's agent memory demo. Use Composio GitHub tools when helpful. "
            "Cite SuperCompress KV savings. Be concise."
        ),
        user_prompt=task,
        context_blocks=context_blocks,
        workflow="openclaw_agent_loop",
    )

    print(f"  Turns: {len(result.turns)}")
    for t in result.turns:
        extra = ""
        if t.memory_stats:
            extra = f" | KV −{t.memory_stats.get('kv_savings_pct', 0):.1f}%"
        print(f"    [{t.phase}] {t.detail}{extra}")

    if result.actions_taken:
        print(f"\n  Composio actions ({len(result.actions_taken)}):")
        for a in result.actions_taken:
            status = "✓" if a.get("success") else "✗"
            print(f"    {status} {a.get('tool')} {json.dumps(a.get('arguments', {}))[:80]}")

    _banner("5 · Agent response")
    print(result.summary or "(no summary)")
    print(f"\n  Memory savings this run: {result.memory_savings_pct:.1f}%")
    print(f"  Model stack: Tavily → Composio → SuperCompress → Nebius\n")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenClaw agent loop — sponsor stack demo")
    parser.add_argument(
        "--task",
        default="Triage my open GitHub PRs and suggest what to ship this week",
        help="Agent task",
    )
    parser.add_argument("--live", action="store_true", help="Use .env keys (not demo fixtures)")
    args = parser.parse_args()
    raise SystemExit(run_loop(task=args.task, live=args.live))


if __name__ == "__main__":
    main()
