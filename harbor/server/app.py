"""FastAPI server — OpenClaw webhook bridge + workflow triggers + landing page."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from harbor.agent.loop import HarborAgent
from harbor.agent.prompts import OPENCLAW_BRIDGE_SYSTEM
from harbor.config import get_settings
from harbor.workflows import run_incident_commander, run_morning_brief

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"

logging.basicConfig(level=get_settings().harbor_log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Harbor Agent",
    description="BuilderShip stack: OpenClaw + Composio + Tavily + Nebius + SuperCompress",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

if (WEB_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")


@app.get("/")
def landing() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api")
def api_redirect():
    return RedirectResponse(url="/docs")


class OpenClawMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    channel: Optional[str] = None


class WorkflowRequest(BaseModel):
    company: str = "Composio"
    focus: str = "AI agents"


class IncidentRequest(BaseModel):
    query: str
    service: str = "production API"


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
def api_morning_brief(req: WorkflowRequest) -> Dict[str, Any]:
    out = run_morning_brief(company=req.company, focus=req.focus)
    return {
        "summary": out.result.summary,
        "memory_savings_pct": out.result.memory_savings_pct,
        "actions": out.result.actions_taken,
    }


@app.post("/workflows/incident")
def api_incident(req: IncidentRequest) -> Dict[str, Any]:
    out = run_incident_commander(req.query, service=req.service)
    return {
        "summary": out.result.summary,
        "memory_savings_pct": out.result.memory_savings_pct,
        "actions": out.result.actions_taken,
    }


@app.post("/openclaw/chat")
def openclaw_chat(payload: OpenClawMessage) -> Dict[str, str]:
    """Handle inbound messages from OpenClaw gateway."""
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
    """Skill manifest for OpenClaw plugin discovery."""
    return {
        "name": "harbor",
        "description": "Builder ops agent — morning briefs, incidents, cross-app automation",
        "endpoints": {
            "chat": "/openclaw/chat",
            "morning_brief": "/workflows/morning-brief",
            "incident": "/workflows/incident",
        },
        "stack": ["openclaw", "composio", "tavily", "nebius", "supercompress"],
    }
