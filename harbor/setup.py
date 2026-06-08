"""Interactive setup wizard — API keys, targets, checkpoint, doctor."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

ROOT = Path(__file__).resolve().parent.parent
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

console = Console()

ENV_FIELDS = [
    ("NEBIUS_API_KEY", "Nebius Token Factory API key", True, "https://tokenfactory.nebius.com"),
    ("COMPOSIO_API_KEY", "Composio API key", True, "https://dashboard.composio.dev"),
    ("TAVILY_API_KEY", "Tavily API key", True, "https://app.tavily.com"),
    ("NEBIUS_MODEL", "Nebius model ID", False, "moonshotai/Kimi-K2-Instruct-0905"),
    ("HARBOR_USER_ID", "Composio user ID (unique per builder)", False, "harbor-builder-001"),
    ("GITHUB_OWNER", "Optional: limit GitHub to one org/user (leave blank = whole account)", False, ""),
    ("GITHUB_REPO", "Optional: limit to one repo (requires GITHUB_OWNER)", False, ""),
    ("SLACK_CHANNEL_ID", "Slack channel ID (C…)", False, ""),
    ("LINEAR_TEAM_ID", "Linear team UUID", False, ""),
]

COMPOSIO_TOOLKITS = ["github", "slack", "linear", "gmail"]


def _read_env() -> Dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    out: Dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def _write_env(values: Dict[str, str]) -> None:
    lines_out: list[str] = []
    seen: set[str] = set()

    if ENV_EXAMPLE.exists():
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                lines_out.append(line)
                continue
            key = line.split("=", 1)[0].strip()
            seen.add(key)
            val = values.get(key)
            if val is not None:
                lines_out.append(f"{key}={val}")
            else:
                lines_out.append(line)

    for key, val in values.items():
        if key not in seen:
            lines_out.append(f"{key}={val}")

    ENV_FILE.write_text("\n".join(lines_out) + "\n", encoding="utf-8")


def _mask(value: str) -> str:
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "****"
    return value[:4] + "…" + value[-4:]


def run_setup(*, open_dashboard: bool = True, skip_connect: bool = False) -> bool:
    """Full interactive setup. Returns True if doctor passes."""
    console.print(
        Panel.fit(
            "[bold cyan]Harbor Setup[/bold cyan]\n"
            "We'll configure API keys, app targets, and verify your stack.\n"
            "Press [dim]Enter[/dim] to keep an existing value.",
            border_style="cyan",
        )
    )

    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        console.print("[green]Created .env from .env.example[/green]")

    existing = _read_env()
    updated = dict(existing)
    updated["HARBOR_DEMO"] = "0"

    console.print("\n[bold]Step 1 — API keys[/bold] (BuilderShip sponsor credits)\n")
    for key, label, secret, default in ENV_FIELDS:
        current = existing.get(key, "")
        hint = f" [dim](default: {default})[/dim]" if default and not secret else ""
        if secret and current:
            prompt_default = _mask(current)
        else:
            prompt_default = current or default or ""

        console.print(f"  [cyan]{label}[/cyan]{hint}")
        if secret and current:
            raw = Prompt.ask(f"  {key}", default="", show_default=False)
            if raw.strip():
                updated[key] = raw.strip()
            elif current:
                updated[key] = current
        else:
            val = Prompt.ask(f"  {key}", default=prompt_default)
            if val.strip() or default:
                updated[key] = val.strip() or default

    _write_env(updated)
    console.print(f"\n[green]✓ Saved {ENV_FILE}[/green]")

    # Reload settings
    from harbor.config import get_settings

    get_settings.cache_clear()

    console.print("\n[bold]Step 2 — SuperCompress checkpoint[/bold]\n")
    ckpt = ROOT / "checkpoints" / "default.pt"
    if not ckpt.exists():
        console.print("  Training ~5K-param memory policy (~30s)…")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "train_memory_checkpoint.py"), "--fast"],
            cwd=str(ROOT),
            check=True,
        )
        console.print("[green]✓ Checkpoint ready[/green]")
    else:
        console.print("[green]✓ Checkpoint already exists[/green]")

    if not skip_connect:
        console.print("\n[bold]Step 3 — Connect Composio apps[/bold] (OAuth in browser)\n")
        if updated.get("COMPOSIO_API_KEY"):
            from harbor.composio import get_composio

            composio = get_composio()
            for toolkit in COMPOSIO_TOOLKITS:
                if Confirm.ask(f"  Connect [cyan]{toolkit}[/cyan] now?", default=True):
                    url = composio.auth_connect_url(toolkit)
                    console.print(f"  → {url}\n")
                    try:
                        webbrowser.open(url)
                    except Exception:
                        pass
        else:
            console.print("[yellow]  Skip — add COMPOSIO_API_KEY first[/yellow]")

    console.print("\n[bold]Step 4 — Verify stack[/bold]\n")
    from harbor.doctor import run_doctor

    ok = run_doctor()

    console.print("\n[bold]Step 5 — Launch[/bold]\n")
    console.print("  [cyan]harbor brief[/cyan]     — run morning brief")
    console.print("  [cyan]harbor serve[/cyan]     — web UI + dashboard")
    console.print("  [cyan]harbor dashboard[/cyan] — open dashboard in browser\n")

    if open_dashboard and Confirm.ask("Open dashboard now? (starts server if needed)", default=True):
        try:
            webbrowser.open("http://127.0.0.1:8787/dashboard")
        except Exception:
            pass
        console.print("[dim]Run: harbor serve[/dim]")

    return ok


def env_status() -> Dict[str, Any]:
    """Masked config for dashboard API."""
    from harbor.config import get_settings

    s = get_settings()
    e = _read_env()
    return {
        "demo_mode": s.demo_mode,
        "harbor_user_id": s.harbor_user_id,
        "github_owner": s.github_owner or None,
        "github_repo": s.github_repo or None,
        "slack_channel_id": s.slack_channel_id or None,
        "linear_team_id": s.linear_team_id or None,
        "nebius_model": s.nebius_model,
        "keys": {
            "nebius": bool(s.has_nebius()),
            "composio": bool(s.has_composio()),
            "tavily": bool(s.has_tavily()),
        },
        "masked": {
            "NEBIUS_API_KEY": _mask(e.get("NEBIUS_API_KEY", "")),
            "COMPOSIO_API_KEY": _mask(e.get("COMPOSIO_API_KEY", "")),
            "TAVILY_API_KEY": _mask(e.get("TAVILY_API_KEY", "")),
        },
        "env_file_exists": ENV_FILE.exists(),
    }
