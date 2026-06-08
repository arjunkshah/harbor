"""Harbor Board — native kanban for plans, features, and build jobs."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
BOARD_FILE = ROOT / ".harbor" / "board.json"

COLUMNS = ["backlog", "ideate", "building", "review", "done"]
COLUMN_LABELS = {
    "backlog": "Backlog",
    "ideate": "Ideate",
    "building": "Building",
    "review": "Review",
    "done": "Done",
}


@dataclass
class BoardCard:
    id: str
    project_id: str
    title: str
    description: str = ""
    column: str = "backlog"
    source_type: str = "manual"  # plan | plan_task | feature | job | prd | manual
    source_id: str = ""
    labels: List[str] = field(default_factory=list)
    done: bool = False
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    (ROOT / ".harbor").mkdir(parents=True, exist_ok=True)


def _load() -> List[BoardCard]:
    _ensure()
    if not BOARD_FILE.exists():
        return []
    try:
        raw = json.loads(BOARD_FILE.read_text(encoding="utf-8"))
        return [BoardCard(**item) for item in raw]
    except (json.JSONDecodeError, TypeError):
        return []


def _save(cards: List[BoardCard]) -> None:
    _ensure()
    BOARD_FILE.write_text(
        json.dumps([c.to_dict() for c in cards[:500]], indent=2),
        encoding="utf-8",
    )


def _find_by_source(cards: List[BoardCard], source_type: str, source_id: str, project_id: str) -> Optional[BoardCard]:
    for c in cards:
        if c.source_type == source_type and c.source_id == source_id and c.project_id == project_id:
            return c
    return None


def list_board(project_id: Optional[str] = None) -> Dict[str, Any]:
    cards = _load()
    if project_id:
        cards = [c for c in cards if c.project_id == project_id]
    grouped = {col: [] for col in COLUMNS}
    for c in cards:
        col = c.column if c.column in COLUMNS else "backlog"
        grouped[col].append(c.to_dict())
    return {
        "columns": [{"id": k, "label": COLUMN_LABELS[k]} for k in COLUMNS],
        "cards": grouped,
        "total": len(cards),
    }


def upsert_card(
    *,
    project_id: str,
    title: str,
    description: str = "",
    column: str = "backlog",
    source_type: str = "manual",
    source_id: str = "",
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    cards = _load()
    existing = _find_by_source(cards, source_type, source_id, project_id) if source_id else None
    now = _now()
    if existing:
        existing.title = title[:200]
        existing.description = description[:8000]
        if column in COLUMNS:
            existing.column = column
        existing.labels = labels or existing.labels
        existing.updated_at = now
        existing.done = column == "done"
        _save(cards)
        return existing.to_dict()

    card = BoardCard(
        id=str(uuid.uuid4())[:8],
        project_id=project_id,
        title=title[:200],
        description=description[:8000],
        column=column if column in COLUMNS else "backlog",
        source_type=source_type,
        source_id=source_id,
        labels=labels or [],
        done=column == "done",
        created_at=now,
        updated_at=now,
    )
    cards.insert(0, card)
    _save(cards)
    return card.to_dict()


def get_card(card_id: str) -> Optional[Dict[str, Any]]:
    for c in _load():
        if c.id == card_id:
            return c.to_dict()
    return None


def create_card(
    *,
    project_id: str,
    title: str,
    description: str = "",
    column: str = "backlog",
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return upsert_card(
        project_id=project_id,
        title=title,
        description=description,
        column=column,
        source_type="manual",
        source_id="",
        labels=labels,
    )


def update_card(
    card_id: str,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    column: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    cards = _load()
    for c in cards:
        if c.id != card_id:
            continue
        if title is not None:
            c.title = title[:200]
        if description is not None:
            c.description = description[:8000]
        if column is not None and column in COLUMNS:
            c.column = column
            c.done = column == "done"
        if labels is not None:
            c.labels = labels
        c.updated_at = _now()
        _save(cards)
        return c.to_dict()
    return None


def delete_card(card_id: str) -> bool:
    cards = _load()
    kept = [c for c in cards if c.id != card_id]
    if len(kept) == len(cards):
        return False
    _save(kept)
    return True


def move_card(card_id: str, column: str) -> Optional[Dict[str, Any]]:
    if column not in COLUMNS:
        return None
    cards = _load()
    for c in cards:
        if c.id != card_id:
            continue
        c.column = column
        c.done = column == "done"
        c.updated_at = _now()
        _save(cards)
        return c.to_dict()
    return None


def move_card_by_source(
    project_id: str,
    source_type: str,
    source_id: str,
    column: str,
) -> Optional[Dict[str, Any]]:
    cards = _load()
    for c in cards:
        if c.project_id == project_id and c.source_type == source_type and c.source_id == source_id:
            return move_card(c.id, column)
    return None


def toggle_card_done(card_id: str, done: bool) -> Optional[Dict[str, Any]]:
    return move_card(card_id, "done" if done else "backlog")


def sync_plan_to_board(plan: Dict[str, Any], project_id: str) -> List[Dict[str, Any]]:
    out = []
    out.append(
        upsert_card(
            project_id=project_id,
            title=plan.get("title", "Plan"),
            description=plan.get("goal", ""),
            column="backlog",
            source_type="plan",
            source_id=plan["id"],
            labels=["plan"],
        )
    )
    for i, task in enumerate(plan.get("tasks", [])):
        text = task.get("text", "") if isinstance(task, dict) else str(task)
        if not text:
            continue
        done = task.get("done", False) if isinstance(task, dict) else False
        out.append(
            upsert_card(
                project_id=project_id,
                title=text[:200],
                description=f"Plan: {plan.get('title')}",
                column="done" if done else "backlog",
                source_type="plan_task",
                source_id=f"{plan['id']}:{i}",
                labels=["task"],
            )
        )
    return out


def sync_features_to_board(project_id: str, features: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out = []
    out.append(
        upsert_card(
            project_id=project_id,
            title="PRD approved",
            description=f"{len(features)} features ready to build",
            column="ideate",
            source_type="prd",
            source_id=project_id,
            labels=["prd"],
        )
    )
    for i, feat in enumerate(features, 1):
        out.append(
            upsert_card(
                project_id=project_id,
                title=feat.get("title", f"Feature {i}"),
                description=feat.get("body", "")[:4000],
                column="ideate",
                source_type="feature",
                source_id=f"{project_id}:feature:{i}",
                labels=["feature"],
            )
        )
    return out


def on_job_status(project_id: str, job: Dict[str, Any]) -> None:
    feat_idx = job.get("meta", {}).get("feature_index")
    if not feat_idx:
        return
    source_id = f"{project_id}:feature:{feat_idx}"
    status = job.get("status", "")
    phase = job.get("phase", "")
    if status == "running":
        move_card_by_source(project_id, "feature", source_id, "building")
    elif status == "completed" and phase == "implement":
        move_card_by_source(project_id, "feature", source_id, "review")
    elif status == "completed" and phase == "review":
        move_card_by_source(project_id, "feature", source_id, "done")
