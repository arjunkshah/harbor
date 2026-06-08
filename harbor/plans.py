"""Builder plans — agent-generated roadmaps stored in workspace."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
PLANS_FILE = ROOT / ".harbor" / "plans.json"


@dataclass
class PlanTask:
    text: str
    done: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Plan:
    id: str
    title: str
    goal: str
    tasks: List[PlanTask] = field(default_factory=list)
    project_id: Optional[str] = None
    created_at: str = ""
    source: str = "agent"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "tasks": [t.to_dict() for t in self.tasks],
            "project_id": self.project_id,
            "created_at": self.created_at,
            "source": self.source,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    (ROOT / ".harbor").mkdir(parents=True, exist_ok=True)


def _load() -> List[Plan]:
    _ensure()
    if not PLANS_FILE.exists():
        return []
    try:
        raw = json.loads(PLANS_FILE.read_text(encoding="utf-8"))
        out: List[Plan] = []
        for item in raw:
            tasks = [PlanTask(**t) for t in item.get("tasks", [])]
            out.append(
                Plan(
                    id=item["id"],
                    title=item["title"],
                    goal=item.get("goal", ""),
                    tasks=tasks,
                    project_id=item.get("project_id"),
                    created_at=item.get("created_at", ""),
                    source=item.get("source", "agent"),
                )
            )
        return out
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def _save(plans: List[Plan]) -> None:
    _ensure()
    PLANS_FILE.write_text(
        json.dumps([p.to_dict() for p in plans[:40]], indent=2),
        encoding="utf-8",
    )


def list_plans(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    plans = _load()
    if project_id:
        plans = [p for p in plans if p.project_id == project_id]
    return [p.to_dict() for p in plans]


def create_plan(
    title: str,
    goal: str,
    tasks: List[str],
    *,
    project_id: Optional[str] = None,
    source: str = "agent",
) -> Dict[str, Any]:
    plan = Plan(
        id=str(uuid.uuid4())[:8],
        title=title.strip() or "Untitled plan",
        goal=goal.strip(),
        tasks=[PlanTask(text=t.strip()) for t in tasks if t.strip()],
        project_id=project_id,
        created_at=_now(),
        source=source,
    )
    plans = _load()
    plans.insert(0, plan)
    _save(plans)
    plan_dict = plan.to_dict()
    try:
        from harbor.sync.engine import on_plan_created

        on_plan_created(plan_dict)
    except Exception:
        pass
    return plan_dict


def toggle_task(plan_id: str, task_index: int) -> Optional[Dict[str, Any]]:
    plans = _load()
    for plan in plans:
        if plan.id != plan_id:
            continue
        if 0 <= task_index < len(plan.tasks):
            plan.tasks[task_index].done = not plan.tasks[task_index].done
            _save(plans)
            plan_dict = plan.to_dict()
            try:
                from harbor.sync.engine import on_task_toggled

                on_task_toggled(plan_id, task_index, plan.tasks[task_index].done)
            except Exception:
                pass
            return plan_dict
    return None


def parse_plan_from_summary(summary: str, goal: str, *, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Extract actionable tasks from agent markdown output."""
    lines = summary.splitlines()
    title = goal[:80] if goal else "Builder plan"
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith(("-", "*", "•")) and len(stripped) < 100:
            if "plan" in stripped.lower() or stripped.endswith(":"):
                continue
            title = stripped.lstrip("#").strip()[:80]
            break
    tasks: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ")):
            tasks.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s", stripped):
            tasks.append(re.sub(r"^\d+\.\s*", "", stripped))
    if not tasks:
        tasks = [ln.strip() for ln in lines if ln.strip()][:5]
    return create_plan(title=title, goal=goal, tasks=tasks[:12], project_id=project_id)
