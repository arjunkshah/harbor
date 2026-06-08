"""Harbor workspace — projects, integration prefs, builder state."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from harbor.integrations import ALL_TOOLKIT_SLUGS, INTEGRATIONS, integration_map
from harbor.setup import _read_env, _write_env

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_FILE = ROOT / ".harbor" / "workspace.json"


@dataclass
class Project:
    id: str
    name: str
    focus: str = "AI agent infrastructure"
    company: str = "Composio"
    notes: str = ""
    created_at: str = ""
    run_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkspaceState:
    active_project_id: Optional[str] = None
    projects: List[Project] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_project_id": self.active_project_id,
            "projects": [p.to_dict() for p in self.projects],
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    (ROOT / ".harbor").mkdir(parents=True, exist_ok=True)


def _load_state() -> WorkspaceState:
    _ensure()
    if not WORKSPACE_FILE.exists():
        default = Project(
            id="default",
            name="My build",
            created_at=_now(),
        )
        state = WorkspaceState(active_project_id="default", projects=[default])
        _save_state(state)
        return state
    try:
        raw = json.loads(WORKSPACE_FILE.read_text(encoding="utf-8"))
        projects = [Project(**p) for p in raw.get("projects", [])]
        return WorkspaceState(
            active_project_id=raw.get("active_project_id"),
            projects=projects,
        )
    except (json.JSONDecodeError, TypeError):
        return WorkspaceState()


def _save_state(state: WorkspaceState) -> None:
    _ensure()
    WORKSPACE_FILE.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def list_projects() -> List[Dict[str, Any]]:
    return [p.to_dict() for p in _load_state().projects]


def get_active_project() -> Optional[Dict[str, Any]]:
    state = _load_state()
    if not state.active_project_id:
        return state.projects[0].to_dict() if state.projects else None
    for p in state.projects:
        if p.id == state.active_project_id:
            return p.to_dict()
    return state.projects[0].to_dict() if state.projects else None


def create_project(name: str, *, focus: str = "", company: str = "", notes: str = "") -> Dict[str, Any]:
    state = _load_state()
    proj = Project(
        id=str(uuid.uuid4())[:8],
        name=name.strip() or "Untitled",
        focus=focus.strip() or "AI agent infrastructure",
        company=company.strip() or "Composio",
        notes=notes.strip(),
        created_at=_now(),
    )
    state.projects.insert(0, proj)
    state.active_project_id = proj.id
    _save_state(state)
    return proj.to_dict()


def set_active_project(project_id: str) -> Dict[str, Any]:
    state = _load_state()
    if not any(p.id == project_id for p in state.projects):
        raise ValueError(f"Unknown project: {project_id}")
    state.active_project_id = project_id
    _save_state(state)
    active = get_active_project()
    assert active is not None
    return active


def bump_project_run(project_id: Optional[str]) -> None:
    if not project_id:
        return
    state = _load_state()
    for p in state.projects:
        if p.id == project_id:
            p.run_count += 1
            break
    _save_state(state)


def set_enabled_toolkits(slugs: List[str]) -> List[str]:
    """Update COMPOSIO_TOOLKITS in .env; returns normalized slugs."""
    valid = {s.lower() for s in ALL_TOOLKIT_SLUGS}
    enabled = [s.lower().strip() for s in slugs if s.lower().strip() in valid]
    if not enabled:
        enabled = ["github"]
    env = _read_env()
    env["COMPOSIO_TOOLKITS"] = ",".join(enabled)
    _write_env(env)
    from harbor.config import get_settings

    get_settings.cache_clear()
    return enabled


def integration_catalog(*, connected: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
    from harbor.config import get_settings

    s = get_settings()
    enabled = set(s.active_toolkits())
    connected = connected or {}
    out: List[Dict[str, Any]] = []
    for info in INTEGRATIONS:
        out.append(
            {
                "slug": info.slug,
                "label": info.label,
                "blurb": info.blurb,
                "recommended": info.recommended,
                "solo_default": info.solo_default,
                "enabled": info.slug in enabled,
                "connected": bool(connected.get(info.slug)),
            }
        )
    return out


def workspace_overview(*, connected: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
    from harbor.store import list_runs, stats

    active = get_active_project()
    runs = list_runs(5)
    project_runs = [r for r in runs if r.get("meta", {}).get("project_id") == (active or {}).get("id")]
    return {
        "tagline": "The workspace for AI builders and vibe coders — connect, plan, ship.",
        "active_project": active,
        "projects": list_projects(),
        "integrations": integration_catalog(connected=connected),
        "stats": stats(),
        "recent_runs": project_runs or runs[:3],
        "differentiators": [
            "Harbor Engine — Tavily → Composio → SuperCompress → Nebius → actions in one loop",
            "Persistent .harbor/ workspace: projects, plans, briefs, run history, KV savings",
            "Plan and execute builder tasks — not just morning briefs or chat",
            "Pick integrations (GitHub-only works; Slack optional for solo builders)",
            "OpenClaw is an optional runtime bridge — Harbor owns orchestration + memory",
        ],
    }


def prompt_catalog() -> List[Dict[str, Any]]:
    from harbor.agent.prompts import (
        BUILDER_PLAN_SYSTEM,
        BUILDER_TASK_SYSTEM,
        INCIDENT_COMMANDER_SYSTEM,
        MORNING_BRIEF_SYSTEM,
        OPENCLAW_BRIDGE_SYSTEM,
    )
    from harbor.config import get_settings
    from harbor.integrations import incident_instructions, morning_brief_instructions

    s = get_settings()
    try:
        from harbor.composio import get_composio

        hub = get_composio()
        status = hub.integration_status()
        slack_ready = hub.slack_delivery_ready()
    except Exception:
        status = {slug: False for slug in ALL_TOOLKIT_SLUGS}
        slack_ready = False

    return [
        {
            "id": "morning_brief",
            "label": "Morning brief",
            "system": MORNING_BRIEF_SYSTEM,
            "dynamic_task": morning_brief_instructions(
                connected=status,
                slack_ready=slack_ready,
            ),
        },
        {
            "id": "incident_commander",
            "label": "Incident commander",
            "system": INCIDENT_COMMANDER_SYSTEM,
            "dynamic_task": incident_instructions(
                connected=status,
                slack_ready=slack_ready,
            ),
        },
        {
            "id": "builder_task",
            "label": "Builder task (run)",
            "system": BUILDER_TASK_SYSTEM,
            "dynamic_task": "User task — gather connected apps, research, act, summarize.",
        },
        {
            "id": "builder_plan",
            "label": "Builder plan",
            "system": BUILDER_PLAN_SYSTEM,
            "dynamic_task": "Plan only — title, goal, numbered shippable tasks.",
        },
        {
            "id": "openclaw_bridge",
            "label": "OpenClaw bridge (optional runtime)",
            "system": OPENCLAW_BRIDGE_SYSTEM,
            "dynamic_task": "Thin gateway session — Harbor runs full gather/compress/act pipeline.",
        },
    ]
