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


def run_doctor_checks(settings: Settings | None = None) -> List[CheckResult]:
    s = settings or get_settings()
    results: List[CheckResult] = []

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

    try:
        t = get_tavily(s)
        bundle = t.search("OpenClaw agent runtime")
        results.append(
            CheckResult("Tavily search", True, f"{len(bundle.hits)} hits for smoke query")
        )
    except Exception as exc:
        results.append(CheckResult("Tavily search", False, str(exc)))

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

    from pathlib import Path

    skill = Path(__file__).resolve().parent.parent / "openclaw" / "SKILL.md"
    env_file = Path(__file__).resolve().parent.parent / ".env"
    env_ok = s.demo_mode or (env_file.exists() and s.has_live_stack())
    results.append(
        CheckResult(
            "Environment",
            env_ok,
            "demo mode" if s.demo_mode else (".env configured" if env_file.exists() else "Run: harbor setup"),
        )
    )
    results.append(
        CheckResult(
            "OpenClaw skill",
            skill.exists(),
            "SKILL.md ready" if skill.exists() else "SKILL.md missing",
        )
    )
    return results


def run_doctor(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    results = run_doctor_checks(s)

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
        console.print("[dim]Run [cyan]harbor setup[/cyan] for live stack.[/dim]")
    elif not all_ok:
        console.print("[dim]Run [cyan]harbor setup[/cyan] to fix configuration.[/dim]")
    return all_ok
