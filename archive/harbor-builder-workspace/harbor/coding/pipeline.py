"""Ideate → approve → PRD → queue → build pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from harbor.agent import HarborAgent
from harbor.agent.prompts import BUILDER_PLAN_SYSTEM, PRD_GENERATION_SYSTEM
from harbor.coding.backends import detect_coding_agents, resolve_agent
from harbor.coding.queue import enqueue_batch, list_jobs, queue_stats
from harbor.coding.scaffold import (
    materialize_features,
    parse_prd_into_features,
    read_project_files,
    write_ideation,
    write_prd,
)
from harbor.config import get_settings
from harbor.workspace import get_active_project, get_project_by_id, set_build_phase, update_project


def ideate(idea: str, *, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Refine an idea with Harbor; append to ideation.md."""
    project = get_project_by_id(project_id) if project_id else get_active_project()
    if not project:
        raise ValueError("No active project — create one in the dashboard first")

    agent = HarborAgent()
    result = agent.builder_task(
        f"Ideation session for a new feature/product:\n\n{idea}\n\n"
        "Help refine: problem, users, MVP scope, risks, what to build first. "
        "Conversational but concrete. End with a clear recommendation.",
        plan_only=False,
    )
    write_ideation(project, f"## Session\n\n**Input:** {idea}\n\n{result.summary or ''}")
    set_build_phase(project["id"], "ideate")
    update_project(project["id"], ideation_summary=(result.summary or "")[:2000])
    return {
        "project_id": project["id"],
        "summary": result.summary,
        "docs": read_project_files(project),
        "phase": "ideate",
    }


def approve_ideation(
    *,
    project_id: Optional[str] = None,
    agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate PRD + feature docs, scaffold folders, queue coding jobs."""
    project = get_project_by_id(project_id) if project_id else get_active_project()
    if not project:
        raise ValueError("No active project")

    docs = read_project_files(project)
    ideation = docs.get("files", {}).get("ideation.md", project.get("ideation_summary", ""))
    if not ideation.strip():
        raise ValueError("Nothing to approve — run ideate first")

    harbor = HarborAgent()
    prd_prompt = (
        f"Project: {project.get('name')}\nFocus: {project.get('focus')}\n\n"
        f"Ideation notes:\n{ideation}\n\n"
        "Produce a full PRD with ### Feature sections (at least 2). "
        "Each feature needs user story + acceptance criteria. "
        "End with ## Coding prompts — numbered one-liner prompts for an AI coding agent."
    )
    result = harbor.run_with_tools(
        PRD_GENERATION_SYSTEM,
        prd_prompt,
        [],
        workflow="prd_generation",
    )
    prd_text = result.summary or ""
    write_prd(project, prd_text)
    features = parse_prd_into_features(prd_text)
    prompt_paths = materialize_features(project, features)

    chosen = resolve_agent(agent or project.get("coding_agent"))
    update_project(
        project["id"],
        coding_agent=chosen,
        build_phase="queued",
        prd_ready=True,
    )
    project = get_project_by_id(project["id"]) or project

    jobs = enqueue_batch(
        project,
        [
            {"title": f["title"], "prompt": f["prompt"], "phase": "implement", "feature_index": i}
            for i, f in enumerate(features, 1)
        ],
        agent=chosen,
    )

    set_build_phase(project["id"], "building")

    sync_result = {}
    try:
        from harbor.sync.engine import sync_approve_bundle

        sync_result = sync_approve_bundle(project, features, prd_excerpt=prd_text[:800])
    except Exception:
        pass

    return {
        "project_id": project["id"],
        "prd_preview": prd_text[:1200],
        "features": len(features),
        "prompt_files": [str(p) for p in prompt_paths],
        "jobs_queued": len(jobs),
        "agent": chosen,
        "docs": read_project_files(project),
        "ecosystem_sync": sync_result,
    }


def queue_custom_prompt(
    prompt: str,
    *,
    project_id: Optional[str] = None,
    agent: Optional[str] = None,
    phase: str = "custom",
) -> Dict[str, Any]:
    from harbor.coding.queue import enqueue_job

    project = get_project_by_id(project_id) if project_id else get_active_project()
    if not project:
        raise ValueError("No active project")
    job = enqueue_job(project, prompt, phase=phase, agent=agent)
    return {"job": job}


def pipeline_status(*, project_id: Optional[str] = None) -> Dict[str, Any]:
    project = get_project_by_id(project_id) if project_id else get_active_project()
    pid = project.get("id") if project else None
    return {
        "project": project,
        "agents": [a.__dict__ for a in detect_coding_agents()],
        "default_agent": resolve_agent(project.get("coding_agent") if project else None),
        "queue": queue_stats(),
        "jobs": list_jobs(project_id=pid, limit=20),
        "docs": read_project_files(project) if project else {},
        "alerts_unread": len(__import__("harbor.coding.notify", fromlist=["list_alerts"]).list_alerts(unread_only=True)),
        "ecosystem_sync": __import__("harbor.sync.engine", fromlist=["sync_status"]).sync_status(
            project_id=pid
        ),
    }
