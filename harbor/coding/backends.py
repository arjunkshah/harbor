"""Detect and invoke Codex / Claude Code CLIs."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from harbor.config import get_settings


@dataclass
class CodingAgentInfo:
    id: str
    label: str
    available: bool
    path: Optional[str]
    version_hint: str = ""


def _version(bin_name: str) -> str:
    try:
        out = subprocess.run(
            [bin_name, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        line = (out.stdout or out.stderr or "").strip().splitlines()
        return line[0][:80] if line else ""
    except Exception:
        return ""


def detect_coding_agents() -> List[CodingAgentInfo]:
    agents = []
    for agent_id, label, bins in [
        ("codex", "Codex", ["codex"]),
        ("claude", "Claude Code", ["claude"]),
        ("cursor", "Cursor Agent", ["cursor-agent", "cursor"]),
    ]:
        path = None
        for b in bins:
            path = shutil.which(b)
            if path:
                break
        agents.append(
            CodingAgentInfo(
                id=agent_id,
                label=label,
                available=bool(path),
                path=path,
                version_hint=_version(path.split("/")[-1]) if path else "",
            )
        )
    return agents


def resolve_agent(preferred: Optional[str] = None) -> str:
    """Pick coding agent: preferred → env → first available → demo."""
    s = get_settings()
    pref = (preferred or s.harbor_coding_agent or "").strip().lower()
    detected = {a.id: a for a in detect_coding_agents()}
    if pref and pref in detected and detected[pref].available:
        return pref
    for agent_id in ("codex", "claude", "cursor"):
        if detected.get(agent_id) and detected[agent_id].available:
            return agent_id
    return "demo"


def build_argv(agent: str, prompt: str, *, workdir: Path) -> List[str]:
    """CLI argv for non-interactive coding agent run."""
    if agent == "codex":
        return ["codex", "exec", "--full-auto", prompt]
    if agent == "claude":
        return ["claude", "-p", prompt]
    if agent == "cursor":
        bin_path = shutil.which("cursor-agent") or shutil.which("cursor")
        if bin_path:
            return [bin_path, "run", prompt]
    raise ValueError(f"Unknown or unavailable coding agent: {agent}")


def run_agent_process(
    agent: str,
    prompt: str,
    *,
    workdir: Path,
    log_path: Path,
    demo_mode: bool = False,
) -> subprocess.Popen:
    workdir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if demo_mode or agent == "demo":
        script = (
            f'echo "[demo] {agent} running in {workdir}" >> "{log_path}"; '
            f'echo "{prompt[:200]}" >> "{log_path}"; '
            f'echo "[demo] completed" >> "{log_path}"; '
            "sleep 2"
        )
        return subprocess.Popen(
            ["bash", "-c", script],
            cwd=str(workdir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    argv = build_argv(agent, prompt, workdir=workdir)
    log_f = open(log_path, "a", encoding="utf-8")
    log_f.write(f"\n--- harbor job ---\n$ {' '.join(argv[:3])} …\n\n")
    log_f.flush()
    return subprocess.Popen(
        argv,
        cwd=str(workdir),
        stdout=log_f,
        stderr=subprocess.STDOUT,
        text=True,
    )
