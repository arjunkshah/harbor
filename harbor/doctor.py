"""Health checks for the full Harbor stack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from rich.console import Console
from rich.table import Table

from harbor.config import Settings, get_settings
from harbor.memory import compare_policies
from harbor.composio import get_composio
from harbor.nebius import get_nebius
from harbor.tavily import get_tavily

console = Console()


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_doctor(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    results: List[CheckResult] = []

    # Memory layer
    try:
        sample = "def authenticate(user):\n    return user.is_active\n\n" * 40
        sample += "class User:\n    def fetch(self):\n        pass\n"
        cmp = compare_policies(sample, "where is authenticate defined", budget_ratio=s.harbor_memory_budget)
        fifo = cmp["FIFO"]
        sc = cmp["SuperCompress"]
        results.append(
            CheckResult(
                "SuperCompress memory",
                True,
                f"FIFO kept {fifo.kept_tokens} tok, SuperCompress {sc.kept_tokens} tok ({sc.policy_name})",
            )
        )
    except Exception as exc:
        results.append(CheckResult("SuperCompress memory", False, str(exc)))

    # Tavily
    try:
        t = get_tavily(s)
        bundle = t.search("OpenClaw agent runtime")
        results.append(
            CheckResult("Tavily search", True, f"{len(bundle.hits)} hits for smoke query")
        )
    except Exception as exc:
        results.append(CheckResult("Tavily search", False, str(exc)))

    # Composio
    try:
        c = get_composio(s)
        gh = c.gather_github()
        tools = c.get_openai_tools()
        results.append(
            CheckResult(
                "Composio toolkits",
                True,
                f"{len(tools)} tools loaded, {len(gh.prs_needing_review)} open PRs in snapshot",
            )
        )
    except Exception as exc:
        results.append(CheckResult("Composio toolkits", False, str(exc)))

    # Nebius
    try:
        n = get_nebius(s)
        resp = n.chat([{"role": "user", "content": "Reply with exactly: harbor-ok"}])
        ok = "harbor" in resp.content.lower() or s.demo_mode
        results.append(
            CheckResult(
                "Nebius inference",
                ok,
                f"model={resp.model}, tokens={resp.usage.get('total_tokens', '?')}",
            )
        )
    except Exception as exc:
        results.append(CheckResult("Nebius inference", False, str(exc)))

    # OpenClaw config
    from pathlib import Path

    skill = Path(__file__).resolve().parent.parent / "openclaw" / "SKILL.md"
    results.append(
        CheckResult(
            "OpenClaw skill",
            skill.exists(),
            str(skill) if skill.exists() else "SKILL.md missing",
        )
    )

    table = Table(title="Harbor Doctor")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Detail")
    all_ok = True
    for r in results:
        if not r.ok:
            all_ok = False
        table.add_row(r.name, "✅" if r.ok else "❌", r.detail)
    console.print(table)

    mode = "DEMO" if s.demo_mode else "LIVE"
    console.print(f"\n[bold]Mode:[/bold] {mode}")
    if s.demo_mode:
        console.print("[dim]Set HARBOR_DEMO=0 and API keys in .env for live stack.[/dim]")
    return all_ok
