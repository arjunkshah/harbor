"""Map Harbor entities → external tool IDs (Linear, GitHub, etc.)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_FILE = ROOT / ".harbor" / "sync_registry.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    (ROOT / ".harbor").mkdir(parents=True, exist_ok=True)


def _load() -> Dict[str, Any]:
    _ensure()
    if not REGISTRY_FILE.exists():
        return {"entries": []}
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, TypeError):
        return {"entries": []}


def _save(data: Dict[str, Any]) -> None:
    _ensure()
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def upsert_entry(
    harbor_type: str,
    harbor_id: str,
    *,
    project_id: str,
    toolkit: str,
    external_id: str,
    external_url: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    data = _load()
    entries: List[Dict[str, Any]] = data.get("entries", [])
    entry = {
        "harbor_type": harbor_type,
        "harbor_id": harbor_id,
        "project_id": project_id,
        "toolkit": toolkit,
        "external_id": external_id,
        "external_url": external_url,
        "meta": meta or {},
        "synced_at": _now(),
    }
    entries = [e for e in entries if not (e["harbor_type"] == harbor_type and e["harbor_id"] == harbor_id and e["toolkit"] == toolkit)]
    entries.insert(0, entry)
    data["entries"] = entries[:200]
    _save(data)
    return entry


def find_entry(harbor_type: str, harbor_id: str, toolkit: str) -> Optional[Dict[str, Any]]:
    for e in _load().get("entries", []):
        if e.get("harbor_type") == harbor_type and e.get("harbor_id") == harbor_id and e.get("toolkit") == toolkit:
            return e
    return None


def list_entries(*, project_id: Optional[str] = None, toolkit: Optional[str] = None) -> List[Dict[str, Any]]:
    entries = _load().get("entries", [])
    if project_id:
        entries = [e for e in entries if e.get("project_id") == project_id]
    if toolkit:
        entries = [e for e in entries if e.get("toolkit") == toolkit]
    return entries


def sync_summary(project_id: Optional[str] = None) -> Dict[str, Any]:
    entries = list_entries(project_id=project_id)
    by_tool: Dict[str, int] = {}
    for e in entries:
        by_tool[e.get("toolkit", "?")] = by_tool.get(e.get("toolkit", "?"), 0) + 1
    return {"total": len(entries), "by_toolkit": by_tool, "recent": entries[:15]}
