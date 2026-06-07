"""High-level workflows exposed to CLI and OpenClaw."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from harbor.agent import AgentRunResult, HarborAgent
from harbor.config import Settings, get_settings


@dataclass
class WorkflowOutput:
    name: str
    result: AgentRunResult
    posted_to_slack: bool = False
    linear_tickets_created: int = 0


def run_morning_brief(
    company: str = "Composio",
    focus: str = "AI agent infrastructure",
    settings: Optional[Settings] = None,
) -> WorkflowOutput:
    agent = HarborAgent(settings)
    result = agent.morning_brief(company=company, focus=focus)
    slack_actions = [a for a in result.actions_taken if "SLACK" in a.get("tool", "")]
    linear_actions = [a for a in result.actions_taken if "LINEAR" in a.get("tool", "")]
    return WorkflowOutput(
        name="morning_brief",
        result=result,
        posted_to_slack=bool(slack_actions),
        linear_tickets_created=len(linear_actions),
    )


def run_incident_commander(
    query: str,
    service: str = "Harbor agent API",
    settings: Optional[Settings] = None,
) -> WorkflowOutput:
    agent = HarborAgent(settings)
    result = agent.incident_commander(query, service_name=service)
    slack_actions = [a for a in result.actions_taken if "SLACK" in a.get("tool", "")]
    linear_actions = [a for a in result.actions_taken if "LINEAR" in a.get("tool", "")]
    return WorkflowOutput(
        name="incident_commander",
        result=result,
        posted_to_slack=bool(slack_actions),
        linear_tickets_created=len(linear_actions),
    )
