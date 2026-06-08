"""Builder workspace workflows — plan and run arbitrary tasks."""

from __future__ import annotations

from typing import Optional

from harbor.agent import HarborAgent
from harbor.config import Settings, get_settings
from harbor.plans import parse_plan_from_summary
from harbor.workflows.morning_brief import WorkflowOutput, _persist, _save_brief_markdown


def run_builder_task(
    query: str,
    settings: Optional[Settings] = None,
    *,
    plan_only: bool = False,
    persist: bool = True,
) -> WorkflowOutput:
    agent = HarborAgent(settings)
    result = agent.builder_task(query, plan_only=plan_only)
    slack_actions = [a for a in result.actions_taken if "SLACK" in a.get("tool", "")]
    linear_actions = [a for a in result.actions_taken if "LINEAR" in a.get("tool", "")]
    name = "builder_plan" if plan_only else "builder_task"
    out = WorkflowOutput(
        name=name,
        result=result,
        posted_to_slack=bool(slack_actions),
        linear_tickets_created=len(linear_actions),
    )
    if result.summary:
        out.brief_path = str(_save_brief_markdown(result.summary, name))
    if persist:
        meta = {"query": query, "plan_only": plan_only}
        if plan_only and result.summary:
            from harbor.workspace import get_active_project

            active = get_active_project()
            plan = parse_plan_from_summary(
                result.summary,
                query,
                project_id=active.get("id") if active else None,
            )
            meta["plan_id"] = plan["id"]
        _persist(out, meta)
    return out
