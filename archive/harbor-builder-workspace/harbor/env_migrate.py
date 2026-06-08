"""One-time .env migrations — deprecated keys, model IDs, etc."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from harbor.nebius_models import DEFAULT_NEBIUS_MODEL, is_deprecated_nebius_model, normalize_nebius_model
from harbor.setup import ENV_FILE, _read_env, _write_env

ROOT = Path(__file__).resolve().parent.parent


def migrate_env(*, write: bool = True) -> Tuple[Dict[str, str], List[str]]:
    """
    Apply in-place migrations to .env values.
    Returns (updated_values, human-readable change messages).
    """
    if not ENV_FILE.exists():
        return {}, []

    env = _read_env()
    changes: List[str] = []

    model = env.get("NEBIUS_MODEL", "")
    if is_deprecated_nebius_model(model):
        new_model = normalize_nebius_model(model)
        env["NEBIUS_MODEL"] = new_model
        changes.append(f"NEBIUS_MODEL: {model} → {new_model} (deprecated)")

    if env.get("HARBOR_DEMO", "").strip().lower() in ("0", "false", "no"):
        pass  # live mode — keep
    elif not env.get("COMPOSIO_TOOLKITS"):
        env["COMPOSIO_TOOLKITS"] = "github,gmail"
        changes.append("COMPOSIO_TOOLKITS: set default github,gmail")

    if write and changes:
        _write_env(env)
        from harbor.config import get_settings

        get_settings.cache_clear()

    return env, changes


def ensure_live_ready() -> List[str]:
    """Run migrations and return messages (for CLI doctor --fix)."""
    _, changes = migrate_env(write=True)
    return changes
