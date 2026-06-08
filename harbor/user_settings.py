"""User-facing Harbor settings (persisted to .env)."""

from __future__ import annotations

from typing import Any, Dict, List

from harbor.setup import _read_env, _write_env

GMAIL_MODES = ("send", "draft")


def get_user_settings() -> Dict[str, Any]:
    env = _read_env()
    mode = (env.get("HARBOR_GMAIL_SYNC_MODE") or "send").strip().lower()
    if mode not in GMAIL_MODES:
        mode = "send"
    auto_sync = (env.get("HARBOR_AUTO_SYNC") or "1").strip().lower() not in ("0", "false", "no")
    return {
        "gmail_sync_mode": mode,
        "gmail_to": (env.get("HARBOR_GMAIL_TO") or "me").strip() or "me",
        "auto_sync": auto_sync,
        "coding_agent": (env.get("HARBOR_CODING_AGENT") or "auto").strip() or "auto",
    }


def update_settings(**fields: Any) -> Dict[str, Any]:
    env = _read_env()
    if "gmail_sync_mode" in fields and fields["gmail_sync_mode"]:
        mode = str(fields["gmail_sync_mode"]).lower()
        if mode in GMAIL_MODES:
            env["HARBOR_GMAIL_SYNC_MODE"] = mode
    if "gmail_to" in fields and fields["gmail_to"] is not None:
        env["HARBOR_GMAIL_TO"] = str(fields["gmail_to"]).strip()
    if "auto_sync" in fields:
        env["HARBOR_AUTO_SYNC"] = "1" if fields["auto_sync"] else "0"
    if "coding_agent" in fields and fields["coding_agent"]:
        env["HARBOR_CODING_AGENT"] = str(fields["coding_agent"]).strip()
    _write_env(env)
    from harbor.config import get_settings as gs

    gs.cache_clear()
    return get_user_settings()
