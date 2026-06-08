"""Persist Harbor workflow runs for the web dashboard."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
HARBOR_DIR = ROOT / ".harbor"
RUNS_FILE = HARBOR_DIR / "runs.json"
MAX_RUNS = 50


@dataclass
class RunRecord:
    id: str
    workflow: str
    created_at: str
    summary: str
    memory_savings_pct: float
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    posted_to_slack: bool = False
    linear_tickets_created: int = 0
    turns: List[Dict[str, str]] = field(default_factory=list)
    status: str = "completed"
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _ensure_dir() -> None:
    HARBOR_DIR.mkdir(parents=True, exist_ok=True)


def _load_all() -> List[Dict[str, Any]]:
    _ensure_dir()
    if not RUNS_FILE.exists():
        return []
    try:
        return json.loads(RUNS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_all(runs: List[Dict[str, Any]]) -> None:
    _ensure_dir()
    RUNS_FILE.write_text(json.dumps(runs[:MAX_RUNS], indent=2), encoding="utf-8")


def save_run(
    workflow: str,
    summary: str,
    memory_savings_pct: float,
    actions_taken: List[Dict[str, Any]],
    *,
    posted_to_slack: bool = False,
    linear_tickets_created: int = 0,
    turns: Optional[List[Dict[str, str]]] = None,
    meta: Optional[Dict[str, Any]] = None,
    status: str = "completed",
) -> RunRecord:
    record = RunRecord(
        id=str(uuid.uuid4())[:8],
        workflow=workflow,
        created_at=datetime.now(timezone.utc).isoformat(),
        summary=summary or "",
        memory_savings_pct=memory_savings_pct,
        actions_taken=actions_taken,
        posted_to_slack=posted_to_slack,
        linear_tickets_created=linear_tickets_created,
        turns=turns or [],
        status=status,
        meta=meta or {},
    )
    runs = _load_all()
    runs.insert(0, record.to_dict())
    _save_all(runs)
    return record


def list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    return _load_all()[:limit]


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    for r in _load_all():
        if r.get("id") == run_id:
            return r
    return None


def stats() -> Dict[str, Any]:
    runs = _load_all()
    if not runs:
        return {"total_runs": 0, "avg_memory_savings": 0.0, "slack_posts": 0, "linear_tickets": 0}
    savings = [float(r.get("memory_savings_pct", 0)) for r in runs]
    return {
        "total_runs": len(runs),
        "avg_memory_savings": round(sum(savings) / len(savings), 1),
        "slack_posts": sum(1 for r in runs if r.get("posted_to_slack")),
        "linear_tickets": sum(int(r.get("linear_tickets_created", 0)) for r in runs),
    }
