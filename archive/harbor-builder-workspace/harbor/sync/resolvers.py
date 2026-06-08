"""Resolve GitHub owner/repo from config or project git remote."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from harbor.config import get_settings


def github_target_for_project(project: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    s = get_settings()
    if s.github_owner and s.github_repo:
        return s.github_owner.strip(), s.github_repo.strip()

    repo_path = (project.get("repo_path") or "").strip()
    if not repo_path:
        return None
    path = Path(repo_path).expanduser().resolve()
    if not (path / ".git").exists():
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        url = (out.stdout or "").strip()
        if not url:
            return None
        m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
        if m:
            return m.group(1), m.group(2).replace(".git", "")
    except Exception:
        pass
    return None
