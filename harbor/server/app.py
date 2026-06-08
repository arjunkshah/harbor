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
from contextlib import asynccontextmanager
import asyncio

from harbor.coding.queue import tick_worker
from harbor.coding.pipeline import (
    approve_ideation,
    ideate,
    pipeline_status,
    queue_custom_prompt,
)
from harbor.coding.notify import list_alerts, mark_alert_read
from harbor.sync.engine import sync_project_ecosystem, sync_status
from harbor.workflows import run_builder_task, run_incident_commander, run_morning_brief

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
LOCAL_DIR = Path(__file__).resolve().parent.parent.parent / "local"

logging.basicConfig(level=get_settings().harbor_log_level)
logger = logging.getLogger(__name__)


async def _coding_worker_loop() -> None:
    while True:
        try:
            tick_worker()
        except Exception as exc:
            logger.debug("coding worker tick: %s", exc)
        await asyncio.sleep(3)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    task = asyncio.create_task(_coding_worker_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Harbor Agent API",
    description="Builder workspace: ops + coding agents (Codex, Claude Code)",
    version="1.1.0",
    docs_url="/api/reference",
    redoc_url="/api/redoc",
    lifespan=_lifespan,
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
    repo_path: str = ""


class ProjectPatchBody(BaseModel):
    repo_path: Optional[str] = None
    coding_agent: Optional[str] = None
    focus: Optional[str] = None
    notes: Optional[str] = None


@app.get("/api/dashboard/projects")
def dashboard_projects() -> Dict[str, Any]:
    return {"active": get_active_project(), "projects": workspace_overview().get("projects", [])}


@app.post("/api/dashboard/projects")
def dashboard_projects_create(body: ProjectBody) -> Dict[str, Any]:
    proj = create_project(
        body.name,
        focus=body.focus,
        company=body.company,
        notes=body.notes,
        repo_path=body.repo_path,
    )
    return {"project": proj}


@app.patch("/api/dashboard/projects/{project_id}")
def dashboard_projects_patch(project_id: str, body: ProjectPatchBody) -> Dict[str, Any]:
    from harbor.workspace import update_project

    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        return {"project": update_project(project_id, **fields)}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


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


class AgentBody(BaseModel):
    query: str
    plan_only: bool = False


@app.post("/api/dashboard/agent")
def dashboard_agent(body: AgentBody) -> Dict[str, Any]:
    out = run_builder_task(body.query, plan_only=body.plan_only)
    r = out.result
    runs = list_runs(1)
    payload: Dict[str, Any] = {
        "run_id": runs[0]["id"] if runs else None,
        "summary": r.summary,
        "memory_savings_pct": r.memory_savings_pct,
        "actions": r.actions_taken,
        "turns": [{"phase": t.phase, "detail": t.detail} for t in r.turns],
        "plan_only": body.plan_only,
    }
    if body.plan_only and runs and runs[0].get("meta", {}).get("plan_id"):
        payload["plan_id"] = runs[0]["meta"]["plan_id"]
    return payload


@app.get("/api/dashboard/plans")
def dashboard_plans() -> Dict[str, Any]:
    from harbor.plans import list_plans

    active = get_active_project()
    pid = active.get("id") if active else None
    return {"plans": list_plans(project_id=pid)}


@app.patch("/api/dashboard/plans/{plan_id}/tasks/{task_index}")
def dashboard_plan_toggle(plan_id: str, task_index: int) -> Dict[str, Any]:
    from harbor.plans import toggle_task

    plan = toggle_task(plan_id, task_index)
    if not plan:
        raise HTTPException(404, "Plan or task not found")
    return {"plan": plan}


# --- Build pipeline (Codex / Claude Code) ---


class IdeateBody(BaseModel):
    idea: str


class ApproveBody(BaseModel):
    agent: Optional[str] = None


class BuildQueueBody(BaseModel):
    prompt: str
    agent: Optional[str] = None
    phase: str = "custom"


@app.get("/api/dashboard/build")
def dashboard_build_status() -> Dict[str, Any]:
    return pipeline_status()


@app.post("/api/dashboard/build/ideate")
def dashboard_build_ideate(body: IdeateBody) -> Dict[str, Any]:
    try:
        return ideate(body.idea)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/dashboard/build/approve")
def dashboard_build_approve(body: ApproveBody) -> Dict[str, Any]:
    try:
        return approve_ideation(agent=body.agent)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/dashboard/build/queue")
def dashboard_build_queue(body: BuildQueueBody) -> Dict[str, Any]:
    try:
        return queue_custom_prompt(body.prompt, agent=body.agent, phase=body.phase)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/dashboard/build/tick")
def dashboard_build_tick() -> Dict[str, Any]:
    job = tick_worker()
    return {"job": job, "status": pipeline_status()}


@app.get("/api/dashboard/alerts")
def dashboard_alerts(unread: bool = False) -> Dict[str, Any]:
    return {"alerts": list_alerts(unread_only=unread)}


@app.patch("/api/dashboard/alerts/{alert_id}/read")
def dashboard_alert_read(alert_id: str) -> Dict[str, Any]:
    alert = mark_alert_read(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return {"alert": alert}


@app.get("/api/dashboard/sync")
def dashboard_sync_status() -> Dict[str, Any]:
    return sync_status()


@app.post("/api/dashboard/sync")
def dashboard_sync_run() -> Dict[str, Any]:
    try:
        return sync_project_ecosystem()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


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
