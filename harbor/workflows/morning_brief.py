"""High-level workflows exposed to CLI and OpenClaw."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from harbor.agent import AgentRunResult, HarborAgent
from harbor.config import Settings, get_settings
from harbor.store import save_run


@dataclass
class WorkflowOutput:
    name: str
    result: AgentRunResult
    posted_to_slack: bool = False
    linear_tickets_created: int = 0


def _persist(out: WorkflowOutput, meta: Optional[dict] = None) -> WorkflowOutput:
    r = out.result
    save_run(
        out.name,
        r.summary,
        r.memory_savings_pct,
        r.actions_taken,
        posted_to_slack=out.posted_to_slack,
        linear_tickets_created=out.linear_tickets_created,
        turns=[{"phase": t.phase, "detail": t.detail} for t in r.turns],
        meta=meta or {},
    )
    return out


def run_morning_brief(
    company: str = "Composio",
    focus: str = "AI agent infrastructure",
    settings: Optional[Settings] = None,
    *,
    persist: bool = True,
) -> WorkflowOutput:
    agent = HarborAgent(settings)
    result = agent.morning_brief(company=company, focus=focus)
    slack_actions = [a for a in result.actions_taken if "SLACK" in a.get("tool", "")]
    linear_actions = [a for a in result.actions_taken if "LINEAR" in a.get("tool", "")]
    out = WorkflowOutput(
        name="morning_brief",
        result=result,
        posted_to_slack=bool(slack_actions),
        linear_tickets_created=len(linear_actions),
    )
    if persist:
        _persist(out, {"company": company, "focus": focus})
    return out


def run_incident_commander(
    query: str,
    service: str = "Harbor agent API",
    settings: Optional[Settings] = None,
    *,
    persist: bool = True,
) -> WorkflowOutput:
    agent = HarborAgent(settings)
    result = agent.incident_commander(query, service_name=service)
    slack_actions = [a for a in result.actions_taken if "SLACK" in a.get("tool", "")]
    linear_actions = [a for a in result.actions_taken if "LINEAR" in a.get("tool", "")]
    out = WorkflowOutput(
        name="incident_commander",
        result=result,
        posted_to_slack=bool(slack_actions),
        linear_tickets_created=len(linear_actions),
    )
    if persist:
        _persist(out, {"query": query, "service": service})
    return out
