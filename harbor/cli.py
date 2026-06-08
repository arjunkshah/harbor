"""Harbor CLI — BuilderShip hackathon entry."""

from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from harbor.config import get_settings
from harbor.doctor import run_doctor
from harbor.setup import run_setup
from harbor.workflows import run_builder_task, run_incident_commander, run_morning_brief

app = typer.Typer(
    name="harbor",
    help="Harbor — builder workspace for AI-native developers (connect · plan · ship)",
    no_args_is_help=True,
)
console = Console()


@app.command()
def setup(
    skip_connect: bool = typer.Option(False, "--skip-connect", help="Skip Composio OAuth prompts"),
) -> None:
    """Interactive setup — API keys, .env, checkpoint, Composio OAuth, doctor."""
    ok = run_setup(open_dashboard=False, skip_connect=skip_connect)
    raise typer.Exit(0 if ok else 1)


@app.command()
def dashboard(
    port: int = typer.Option(8787, help="Server port"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open dashboard in browser"),
) -> None:
    """Open the Harbor dashboard (starts server if not running)."""
    url = f"http://127.0.0.1:{port}/dashboard"
    if open_browser:
        console.print(f"[cyan]Opening[/cyan] {url}")
        console.print("[dim]Starting server — press Ctrl+C to stop[/dim]\n")
        try:
            webbrowser.open(url)
        except Exception:
            pass
    import uvicorn

    uvicorn.run("harbor.server.app:app", host="0.0.0.0", port=port, reload=False)


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


@app.command("run")
def run_task(
    query: str = typer.Argument(..., help="Builder task for Harbor agent"),
    plan: bool = typer.Option(False, "--plan", help="Plan only — saves to .harbor/plans.json"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON result"),
) -> None:
    """Run a general builder task — connect, plan, act across your stack."""
    label = "Harbor Plan" if plan else "Harbor Run"
    console.print(f"[bold cyan]{label}[/bold cyan] — {query}\n")
    out = run_builder_task(query, plan_only=plan)
    _print_workflow_output(out, json_out)


@app.command("incident")
def incident(
    query: str = typer.Argument(..., help="Incident description"),
    service: str = typer.Option("production API", help="Affected service"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON result"),
) -> None:
    """Incident commander: Tavily intel → connected apps (Slack/Linear/GitHub if linked)."""
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
    console.print("\n[dim]Ready for real keys? Run:[/dim] [cyan]harbor setup[/cyan]")


@app.command("integrations")
def integrations_cmd(
    action: str = typer.Argument("list", help="list | set"),
    toolkits: Optional[str] = typer.Argument(None, help="For set: github,linear,gmail,slack"),
) -> None:
    """List or choose which Composio integrations Harbor uses."""
    from harbor.composio import get_composio
    from harbor.workspace import integration_catalog, set_enabled_toolkits

    hub = get_composio()
    connected = hub.integration_status()

    if action == "list":
        rows = integration_catalog(connected=connected)
        for row in rows:
            flags = []
            if row["enabled"]:
                flags.append("enabled")
            if row["connected"]:
                flags.append("connected")
            flag_txt = f" [{', '.join(flags)}]" if flags else ""
            console.print(f"  [cyan]{row['slug']}[/cyan] — {row['label']}{flag_txt}")
            console.print(f"    [dim]{row['blurb']}[/dim]")
        console.print("\n[dim]Enable:[/dim] harbor integrations set github,linear,gmail")
        console.print("[dim]Connect OAuth:[/dim] harbor connect github")
        return

    if action == "set":
        if not toolkits:
            console.print("[red]Usage:[/red] harbor integrations set github,linear")
            raise typer.Exit(1)
        slugs = [s.strip() for s in toolkits.split(",") if s.strip()]
        enabled = set_enabled_toolkits(slugs)
        hub.invalidate_cache()
        get_settings.cache_clear()
        console.print(f"[green]✓ Enabled:[/green] {', '.join(enabled)}")
        console.print("[dim]Connect OAuth for each: harbor connect <slug>[/dim]")
        return

    console.print("[red]Unknown action.[/red] Use list or set.")
    raise typer.Exit(1)


@app.command("connect")
def connect(
    toolkit: str = typer.Argument(..., help="github | slack | linear | gmail"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open OAuth link in browser"),
) -> None:
    """Open Composio OAuth to connect GitHub, Slack, Linear, or Gmail."""
    import webbrowser

    from harbor.composio import get_composio

    c = get_composio()
    result = c.auth_connect(toolkit)
    uid = get_settings().harbor_user_id

    if result.already_connected:
        console.print(Panel(f"[green]✓ {toolkit}[/green] is already connected for [cyan]{uid}[/cyan]"))
        return
    if result.error or not result.redirect_url:
        console.print(Panel(f"[red]Could not connect {toolkit}[/red]\n\n{result.error or 'No redirect URL'}"))
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"Connect [bold]{toolkit}[/bold] for user [cyan]{uid}[/cyan]\n\n"
            f"{result.redirect_url}\n\n"
            "[dim]Complete OAuth in your browser. Harbor uses your whole connected account.[/dim]"
        )
    )
    if open_browser:
        try:
            webbrowser.open(result.redirect_url)
        except Exception:
            pass


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8787, help="Bind port"),
) -> None:
    """Start web server — landing, docs, dashboard, API."""
    import uvicorn

    console.print(f"[cyan]Harbor[/cyan] → http://127.0.0.1:{port}")
    console.print(f"  Dashboard  http://127.0.0.1:{port}/dashboard")
    console.print(f"  Docs       http://127.0.0.1:{port}/docs")
    console.print(f"  API        http://127.0.0.1:{port}/api/reference\n")
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
    if out.brief_path:
        console.print(f"[dim]Saved to[/dim] [cyan]{out.brief_path}[/cyan]")
    console.print(
        f"[dim]Composio actions: {len(r.actions_taken)} | "
        f"Slack: {out.posted_to_slack} | Linear: {out.linear_tickets_created}[/dim]"
    )
    console.print(f"[dim]View in dashboard:[/dim] [cyan]harbor dashboard[/cyan]")
    for t in r.turns:
        console.print(f"  [cyan]{t.phase}[/cyan] {t.detail}")


if __name__ == "__main__":
    app()
