"""FastAPI server — public site, user dashboard, OpenClaw bridge."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from harbor.agent.loop import HarborAgent
from harbor.agent.prompts import OPENCLAW_BRIDGE_SYSTEM
from harbor.config import get_settings
from harbor.setup import env_status
from harbor.store import get_run, list_runs, stats
from harbor.workspace import (
    create_project,
    get_active_project,
    integration_catalog,
    prompt_catalog,
    set_active_project,
    set_enabled_toolkits,
    workspace_overview,
)
from harbor.workflows import run_incident_commander, run_morning_brief

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
LOCAL_DIR = Path(__file__).resolve().parent.parent.parent / "local"

logging.basicConfig(level=get_settings().harbor_log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Harbor Agent API",
    description="BuilderShip stack: OpenClaw + Composio + Tavily + Nebius + SuperCompress",
    version="1.0.0",
    docs_url="/api/reference",
    redoc_url="/api/redoc",
)

if (WEB_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")

if (LOCAL_DIR / "assets").is_dir():
    app.mount("/local/assets", StaticFiles(directory=LOCAL_DIR / "assets"), name="local_assets")


def _page(name: str) -> FileResponse:
    path = WEB_DIR / name
    if not path.exists():
        raise HTTPException(404, f"Page not found: {name}")
    return FileResponse(path)


@app.get("/")
def landing() -> FileResponse:
    return _page("index.html")


@app.get("/docs")
def docs_page() -> FileResponse:
    return _page("docs.html")


@app.get("/dashboard")
def dashboard_page() -> FileResponse:
    path = LOCAL_DIR / "dashboard.html"
    if not path.exists():
        raise HTTPException(404, "Local dashboard not found")
    return FileResponse(path)


@app.get("/setup")
def setup_page() -> FileResponse:
    return RedirectResponse("/docs#setup")


# --- Dashboard API ---


@app.get("/api/dashboard/status")
def dashboard_status() -> Dict[str, Any]:
    s = get_settings()
    from harbor.composio import get_composio
    from harbor.doctor import run_doctor_checks

    composio = get_composio()
    connected = composio.integration_status()
    checks = run_doctor_checks(s)
    return {
        "config": env_status(),
        "integrations": {
            "nebius": s.has_nebius(),
            "composio": s.has_composio(),
            "tavily": s.has_tavily(),
            "demo_mode": s.demo_mode,
        },
        "toolkits": integration_catalog(connected=connected),
        "workspace": workspace_overview(connected=connected),
        "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in checks],
        "stats": stats(),
    }


class IntegrationsBody(BaseModel):
    enabled: List[str]


@app.get("/api/dashboard/integrations")
def dashboard_integrations() -> Dict[str, Any]:
    from harbor.composio import get_composio

    connected = get_composio().integration_status()
    return {"toolkits": integration_catalog(connected=connected)}


@app.put("/api/dashboard/integrations")
def dashboard_integrations_update(body: IntegrationsBody) -> Dict[str, Any]:
    from harbor.composio import get_composio

    enabled = set_enabled_toolkits(body.enabled)
    get_composio().invalidate_cache()
    get_settings.cache_clear()
    connected = get_composio().integration_status()
    return {"enabled": enabled, "toolkits": integration_catalog(connected=connected)}


@app.get("/api/dashboard/integrations/{slug}/connect-url")
def dashboard_connect_url(slug: str) -> Dict[str, Any]:
    from harbor.composio import get_composio

    result = get_composio().auth_connect(slug)
    if result.error and not result.already_connected:
        raise HTTPException(400, result.error)
    return {
        "slug": slug,
        "already_connected": result.already_connected,
        "redirect_url": result.redirect_url,
    }


class ProjectBody(BaseModel):
    name: str
    focus: str = ""
    company: str = ""
    notes: str = ""


@app.get("/api/dashboard/projects")
def dashboard_projects() -> Dict[str, Any]:
    return {"active": get_active_project(), "projects": workspace_overview().get("projects", [])}


@app.post("/api/dashboard/projects")
def dashboard_projects_create(body: ProjectBody) -> Dict[str, Any]:
    proj = create_project(body.name, focus=body.focus, company=body.company, notes=body.notes)
    return {"project": proj}


@app.post("/api/dashboard/projects/{project_id}/activate")
def dashboard_projects_activate(project_id: str) -> Dict[str, Any]:
    try:
        return {"project": set_active_project(project_id)}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.get("/api/dashboard/prompts")
def dashboard_prompts() -> Dict[str, Any]:
    return {"prompts": prompt_catalog()}


@app.get("/api/dashboard/workspace")
def dashboard_workspace() -> Dict[str, Any]:
    from harbor.composio import get_composio

    return workspace_overview(connected=get_composio().integration_status())


@app.get("/api/dashboard/runs")
def dashboard_runs(limit: int = 20) -> Dict[str, Any]:
    return {"runs": list_runs(limit=limit)}


@app.get("/api/dashboard/runs/{run_id}")
def dashboard_run_detail(run_id: str) -> Dict[str, Any]:
    run = get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


class BriefBody(BaseModel):
    company: str = "Composio"
    focus: str = Field(default="AI agent infrastructure")


class IncidentBody(BaseModel):
    query: str
    service: str = "production API"


@app.post("/api/dashboard/brief")
def dashboard_brief(body: BriefBody) -> Dict[str, Any]:
    out = run_morning_brief(company=body.company, focus=body.focus)
    r = out.result
    runs = list_runs(1)
    return {
        "run_id": runs[0]["id"] if runs else None,
        "summary": r.summary,
        "memory_savings_pct": r.memory_savings_pct,
        "actions": r.actions_taken,
        "posted_to_slack": out.posted_to_slack,
        "linear_tickets_created": out.linear_tickets_created,
        "turns": [{"phase": t.phase, "detail": t.detail} for t in r.turns],
    }


@app.post("/api/dashboard/incident")
def dashboard_incident(body: IncidentBody) -> Dict[str, Any]:
    out = run_incident_commander(body.query, service=body.service)
    r = out.result
    runs = list_runs(1)
    return {
        "run_id": runs[0]["id"] if runs else None,
        "summary": r.summary,
        "memory_savings_pct": r.memory_savings_pct,
        "actions": r.actions_taken,
        "turns": [{"phase": t.phase, "detail": t.detail} for t in r.turns],
    }


# --- Legacy / OpenClaw ---


class OpenClawMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    channel: Optional[str] = None


@app.get("/health")
def health() -> Dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "demo_mode": s.demo_mode,
        "integrations": {
            "nebius": s.has_nebius(),
            "composio": s.has_composio(),
            "tavily": s.has_tavily(),
        },
    }


@app.post("/workflows/morning-brief")
def api_morning_brief(req: BriefBody) -> Dict[str, Any]:
    return dashboard_brief(req)


@app.post("/workflows/incident")
def api_incident(req: IncidentBody) -> Dict[str, Any]:
    return dashboard_incident(req)


@app.post("/openclaw/chat")
def openclaw_chat(payload: OpenClawMessage) -> Dict[str, str]:
    agent = HarborAgent()
    from harbor.tavily import get_tavily

    tavily = get_tavily()
    research = tavily.search_and_answer(payload.message)
    composio = agent.composio.gather_all()
    result = agent.run_with_tools(
        OPENCLAW_BRIDGE_SYSTEM,
        payload.message,
        [research.to_context_block(), *composio.all_context_blocks()],
        workflow="openclaw_chat",
    )
    return {"response": result.summary, "memory_savings_pct": str(result.memory_savings_pct)}


@app.get("/openclaw/manifest")
def openclaw_manifest() -> Dict[str, Any]:
    return {
        "name": "harbor",
        "description": "Builder ops agent — morning briefs, incidents, cross-app automation",
        "endpoints": {
            "chat": "/openclaw/chat",
            "morning_brief": "/api/dashboard/brief",
            "incident": "/api/dashboard/incident",
        },
        "stack": ["openclaw", "composio", "tavily", "nebius", "supercompress"],
    }
