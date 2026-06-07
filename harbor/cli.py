"""Harbor CLI — BuilderShip hackathon entry."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from harbor.config import get_settings
from harbor.doctor import run_doctor
from harbor.workflows import run_incident_commander, run_morning_brief

app = typer.Typer(
    name="harbor",
    help="Harbor — builder ops agent (OpenClaw + Composio + Tavily + Nebius + SuperCompress)",
    no_args_is_help=True,
)
console = Console()


@app.command()
def doctor() -> None:
    """Verify all integrations: memory, Tavily, Composio, Nebius, OpenClaw skill."""
    ok = run_doctor()
    raise typer.Exit(0 if ok else 1)


@app.command("brief")
def morning_brief(
    company: str = typer.Option("Composio", help="Company for competitive intel"),
    focus: str = typer.Option("AI agent infrastructure", help="Research focus"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON result"),
) -> None:
    """Run the full morning brief workflow across the entire stack."""
    console.print("[bold cyan]Harbor Morning Brief[/bold cyan] — gathering + compressing + acting\n")
    out = run_morning_brief(company=company, focus=focus)
    _print_workflow_output(out, json_out)


@app.command("incident")
def incident(
    query: str = typer.Argument(..., help="Incident description"),
    service: str = typer.Option("production API", help="Affected service"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON result"),
) -> None:
    """Incident commander: Tavily intel → Slack + Linear + GitHub via Composio."""
    console.print(f"[bold red]Harbor Incident Commander[/bold red] — {query}\n")
    out = run_incident_commander(query, service=service)
    _print_workflow_output(out, json_out)


@app.command("demo")
def demo() -> None:
    """Run full demo in fixture mode (no API keys required)."""
    import os

    os.environ["HARBOR_DEMO"] = "1"
    get_settings.cache_clear()
    console.print("[bold green]Demo mode[/bold green] — running doctor + morning brief\n")
    run_doctor()
    console.print()
    out = run_morning_brief()
    _print_workflow_output(out, False)


@app.command("connect")
def connect(
    toolkit: str = typer.Argument(..., help="github | slack | linear | gmail"),
) -> None:
    """Print Composio OAuth connect instructions for a toolkit."""
    from harbor.composio import get_composio

    c = get_composio()
    url = c.auth_connect_url(toolkit)
    console.print(Panel(f"Connect [bold]{toolkit}[/bold] for user [cyan]{get_settings().harbor_user_id}[/cyan]\n\n{url}"))


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8787, help="Bind port"),
) -> None:
    """Start FastAPI server for OpenClaw webhook bridge."""
    import uvicorn

    uvicorn.run("harbor.server.app:app", host=host, port=port, reload=False)


def _print_workflow_output(out, json_out: bool) -> None:
    r = out.result
    if json_out:
        payload = {
            "workflow": out.name,
            "summary": r.summary,
            "memory_savings_pct": r.memory_savings_pct,
            "actions": r.actions_taken,
            "posted_to_slack": out.posted_to_slack,
            "linear_tickets": out.linear_tickets_created,
            "turns": [{"phase": t.phase, "detail": t.detail} for t in r.turns],
        }
        console.print_json(json.dumps(payload, indent=2))
        return

    console.print(Panel(Markdown(r.summary or "_No summary_"), title="Brief"))
    console.print(f"\n[dim]SuperCompress KV savings: {r.memory_savings_pct:.1f}%[/dim]")
    console.print(f"[dim]Composio actions: {len(r.actions_taken)} | Slack: {out.posted_to_slack} | Linear: {out.linear_tickets_created}[/dim]")
    for t in r.turns:
        console.print(f"  [cyan]{t.phase}[/cyan] {t.detail}")


if __name__ == "__main__":
    app()
