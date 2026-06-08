"""Alerts when coding jobs finish or need you."""

from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
ALERTS_FILE = ROOT / ".harbor" / "alerts.json"
MAX_ALERTS = 40


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    (ROOT / ".harbor").mkdir(parents=True, exist_ok=True)


def _load() -> List[Dict[str, Any]]:
    _ensure()
    if not ALERTS_FILE.exists():
        return []
    try:
        return json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, TypeError):
        return []


def _save(items: List[Dict[str, Any]]) -> None:
    _ensure()
    ALERTS_FILE.write_text(json.dumps(items[:MAX_ALERTS], indent=2), encoding="utf-8")


def push_alert(
    title: str,
    message: str,
    *,
    level: str = "info",
    project_id: Optional[str] = None,
    job_id: Optional[str] = None,
    needs_you: bool = False,
) -> Dict[str, Any]:
    alert = {
        "id": f"alert-{datetime.now(timezone.utc).strftime('%H%M%S%f')[:12]}",
        "title": title,
        "message": message,
        "level": level,
        "project_id": project_id,
        "job_id": job_id,
        "needs_you": needs_you,
        "read": False,
        "created_at": _now(),
    }
    items = _load()
    items.insert(0, alert)
    _save(items)
    _desktop_notify(title, message)
    _maybe_slack(title, message, needs_you=needs_you)
    return alert


def list_alerts(unread_only: bool = False) -> List[Dict[str, Any]]:
    items = _load()
    if unread_only:
        return [a for a in items if not a.get("read")]
    return items


def mark_alert_read(alert_id: str) -> Optional[Dict[str, Any]]:
    items = _load()
    for a in items:
        if a.get("id") == alert_id:
            a["read"] = True
            _save(items)
            return a
    return None


def _desktop_notify(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        return
    safe_title = title.replace('"', "'")[:120]
    safe_msg = message.replace('"', "'")[:240]
    script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "Glass"'
    try:
        subprocess.run(["osascript", "-e", script], check=False, timeout=5)
    except Exception:
        pass


def _maybe_slack(title: str, message: str, *, needs_you: bool) -> None:
    try:
        from harbor.config import get_settings
        from harbor.composio import get_composio

        s = get_settings()
        if not s.slack_configured() or not s.slack_ready():
            return
        hub = get_composio()
        prefix = "🟡 *Needs you*" if needs_you else "✅"
        hub.post_slack_digest(f"{prefix} *Harbor Build* — {title}\n{message[:500]}")
    except Exception:
        pass
