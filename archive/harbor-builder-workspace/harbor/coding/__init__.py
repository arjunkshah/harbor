"""Coding agent orchestration — Codex, Claude Code, queue, scaffold."""

from harbor.coding.backends import detect_coding_agents, resolve_agent
from harbor.coding.pipeline import (
    approve_ideation,
    ideate,
    pipeline_status,
    queue_custom_prompt,
)
from harbor.coding.queue import list_jobs, tick_worker

__all__ = [
    "approve_ideation",
    "detect_coding_agents",
    "ideate",
    "list_jobs",
    "pipeline_status",
    "queue_custom_prompt",
    "resolve_agent",
    "tick_worker",
]
