"""Integration catalog — tuned for solo builders, not enterprise teams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class IntegrationInfo:
    slug: str
    label: str
    blurb: str
    recommended: bool
    solo_default: bool  # included in default COMPOSIO_TOOLKITS


INTEGRATIONS: List[IntegrationInfo] = [
    IntegrationInfo(
        slug="github",
        label="GitHub",
        blurb="Your whole account — PRs, issues, commits across all repos",
        recommended=True,
        solo_default=True,
    ),
    IntegrationInfo(
        slug="linear",
        label="Linear",
        blurb="Personal task board — auto-picks your default team",
        recommended=False,
        solo_default=True,
    ),
    IntegrationInfo(
        slug="gmail",
        label="Gmail",
        blurb="Your inbox — unread and important threads",
        recommended=False,
        solo_default=True,
    ),
    IntegrationInfo(
        slug="slack",
        label="Slack",
        blurb="Optional — broadcast briefs to a team channel (skip if you work solo)",
        recommended=False,
        solo_default=False,
    ),
]

ALL_TOOLKIT_SLUGS = [i.slug for i in INTEGRATIONS]
SOLO_DEFAULT_TOOLKITS = [i.slug for i in INTEGRATIONS if i.solo_default]


def integration_map() -> Dict[str, IntegrationInfo]:
    return {i.slug: i for i in INTEGRATIONS}


def morning_brief_instructions(
    *,
    connected: Dict[str, bool],
    slack_ready: bool,
) -> str:
    """Dynamic task list based on what the builder actually connected."""
    sections: List[str] = []
    if connected.get("github"):
        sections.append("GitHub")
    if connected.get("linear"):
        sections.append("Linear")
    if connected.get("gmail"):
        sections.append("Gmail")
    sections.extend(["Market intel", "Actions"])

    actions: List[str] = [
        f"Write a morning brief under 400 words with sections: {', '.join(sections)}.",
        "Be specific — cite PR numbers, ticket IDs, and URLs when available.",
    ]

    if connected.get("slack") and slack_ready:
        actions.append("Post the brief to Slack using SLACK_SEND_MESSAGE.")
    else:
        actions.append(
            "Put the full brief in your final reply — the builder reads it in the terminal "
            "(no Slack required for solo use)."
        )

    if connected.get("linear"):
        actions.append(
            "Create Linear follow-up tickets only for items blocked more than 24 hours."
        )

    if connected.get("gmail"):
        actions.append("Flag any urgent unanswered emails in the Actions section.")

    return "\n".join(f"{i}. {line}" for i, line in enumerate(actions, start=1))


def incident_instructions(
    *,
    connected: Dict[str, bool],
    slack_ready: bool,
) -> str:
    steps: List[str] = ["Write a severity assessment with blast radius."]
    if connected.get("slack") and slack_ready:
        steps.append("Post a status update to Slack.")
    if connected.get("linear"):
        steps.append("Create or update a Linear incident ticket.")
    if connected.get("github"):
        steps.append("If a matching GitHub issue exists, add a comment.")
    if not any(connected.get(k) for k in ("slack", "linear", "github")):
        steps.append("Deliver the full incident report in your final reply.")
    return "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
