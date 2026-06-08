"""Project docs scaffold — ideation, PRD, feature folders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent


def project_docs_root(project: Dict[str, Any]) -> Path:
    """Harbor docs live in repo or .harbor/projects/{id}/."""
    repo = (project.get("repo_path") or "").strip()
    if repo:
        base = Path(repo).expanduser().resolve()
        return base / "docs" / "harbor"
    return ROOT / ".harbor" / "projects" / project["id"]


def project_workdir(project: Dict[str, Any]) -> Path:
    repo = (project.get("repo_path") or "").strip()
    if repo:
        return Path(repo).expanduser().resolve()
    return project_docs_root(project)


def ensure_git_repo(path: Path) -> None:
    """Codex requires a git repo."""
    if (path / ".git").exists():
        return
    import subprocess

    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=False)


def scaffold_tree(project: Dict[str, Any]) -> Path:
    root = project_docs_root(project)
    for sub in ("features", "prompts", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    work = project_workdir(project)
    ensure_git_repo(work)
    return root


def write_ideation(project: Dict[str, Any], content: str) -> Path:
    root = scaffold_tree(project)
    path = root / "ideation.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text((existing + "\n\n" + content).strip() + "\n", encoding="utf-8")
    return path


def write_prd(project: Dict[str, Any], prd_text: str) -> Path:
    root = scaffold_tree(project)
    path = root / "prd.md"
    path.write_text(prd_text.strip() + "\n", encoding="utf-8")
    return path


def parse_prd_into_features(prd_text: str) -> List[Dict[str, str]]:
    """Split PRD into feature docs and coding prompts."""
    features: List[Dict[str, str]] = []
    chunks = re.split(r"\n(?=###\s+|\n##\s+Feature)", prd_text, flags=re.I)
    idx = 1
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 40:
            continue
        title_match = re.search(r"^#+\s*(.+)$", chunk, re.M)
        title = (title_match.group(1).strip() if title_match else f"Feature {idx}")[:80]
        features.append({"title": title, "body": chunk, "prompt": _feature_to_prompt(title, chunk)})
        idx += 1
    if not features and prd_text.strip():
        features.append(
            {
                "title": "Implementation",
                "body": prd_text,
                "prompt": _feature_to_prompt("Implementation", prd_text),
            }
        )
    return features


def _feature_to_prompt(title: str, body: str) -> str:
    return (
        f"Implement Harbor project feature: {title}\n\n"
        f"Read docs/harbor/prd.md and this feature spec:\n\n{body}\n\n"
        "Work in the repo. Write clean, shippable code. Run tests if they exist. "
        "When done, summarize what you changed."
    )


def materialize_features(project: Dict[str, Any], features: List[Dict[str, str]]) -> List[Path]:
    root = scaffold_tree(project)
    paths: List[Path] = []
    for i, feat in enumerate(features, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", feat["title"].lower()).strip("-")[:40] or f"feature-{i}"
        feat_path = root / "features" / f"{i:02d}-{slug}.md"
        feat_path.write_text(feat["body"].strip() + "\n", encoding="utf-8")
        prompt_path = root / "prompts" / f"{i:02d}-{slug}.md"
        prompt_path.write_text(feat["prompt"].strip() + "\n", encoding="utf-8")
        paths.append(prompt_path)
    return paths


def read_project_files(project: Dict[str, Any]) -> Dict[str, Any]:
    root = project_docs_root(project)
    out: Dict[str, Any] = {"docs_root": str(root), "files": {}}
    if not root.exists():
        return out
    for name in ("ideation.md", "prd.md"):
        p = root / name
        if p.exists():
            out["files"][name] = p.read_text(encoding="utf-8")[:8000]
    features = sorted((root / "features").glob("*.md")) if (root / "features").exists() else []
    out["features"] = [f.name for f in features]
    return out
