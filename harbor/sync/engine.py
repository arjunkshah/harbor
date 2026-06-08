"""Push Harbor state to Board + connected Composio apps (not Linear by default)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from harbor.board import (
    move_card_by_source,
    on_job_status,
    sync_features_to_board,
    sync_plan_to_board,
)
from harbor.config import get_settings
from harbor.sync.registry import find_entry, list_entries, sync_summary, upsert_entry
from harbor.sync.resolvers import github_target_for_project
from harbor.workspace import get_active_project, get_project_by_id


def _hub():
    from harbor.composio import get_composio

    return get_composio()


def _connected() -> Dict[str, bool]:
    return _hub().integration_status()


def _harbor_footer(project: Dict[str, Any], *, docs_hint: str = "") -> str:
    lines = ["", "---", f"*Synced from Harbor · `{project.get('name', '')}`*"]
    if docs_hint:
        lines.append(f"Docs: `{docs_hint}`")
    lines.append("Board: Harbor dashboard → Board")
    return "\n".join(lines)


def _extract_url(data: Any, toolkit: str) -> str:
    if not isinstance(data, dict):
        return ""
    if toolkit == "github":
        return str(data.get("html_url") or data.get("url") or "")
    return ""


def _extract_id(data: Any, toolkit: str) -> str:
    if not isinstance(data, dict):
        return ""
    if toolkit == "github":
        return str(data.get("number") or data.get("id") or "")
    return ""


def sync_plan(plan: Dict[str, Any], *, project: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    project = project or (get_project_by_id(plan.get("project_id")) if plan.get("project_id") else get_active_project())
    if not project:
        raise ValueError("No project for plan sync")

    hub = _hub()
    status = _connected()
    results: List[Dict[str, Any]] = []

    board_cards = sync_plan_to_board(plan, project["id"])
    results.append({"toolkit": "harbor_board", "type": "plan", "ok": True, "count": len(board_cards)})

    gh_target = github_target_for_project(project) if status.get("github") else None
    for i, task in enumerate(plan.get("tasks", [])):
        text = task.get("text", "") if isinstance(task, dict) else str(task)
        if not text:
            continue
        task_key = f"{plan['id']}:{i}"
        if gh_target and not find_entry("plan_task", task_key, "github"):
            owner, repo = gh_target
            body = f"Harbor plan task\n\n{text}{_harbor_footer(project, docs_hint='docs/harbor/')}"
            r = hub.create_github_issue(owner, repo, f"[Harbor] {text[:120]}", body, labels=["harbor"])
            if r.success:
                upsert_entry(
                    "plan_task",
                    task_key,
                    project_id=project["id"],
                    toolkit="github",
                    external_id=_extract_id(r.data, "github") or str(i),
                    external_url=_extract_url(r.data, "github"),
                    meta={"owner": owner, "repo": repo},
                )
                results.append({"toolkit": "github", "type": "plan_task", "ok": True, "title": text[:80]})

    _broadcast_summary(
        project,
        f"Plan synced: **{plan.get('title')}** — {len(plan.get('tasks', []))} cards on Harbor Board.",
        results,
    )
    return {"plan_id": plan["id"], "results": results, "registry": sync_summary(project["id"])}


def sync_prd_features(
    project: Dict[str, Any],
    features: List[Dict[str, str]],
    *,
    prd_excerpt: str = "",
) -> Dict[str, Any]:
    hub = _hub()
    status = _connected()
    results: List[Dict[str, Any]] = []

    board_cards = sync_features_to_board(project["id"], features)
    results.append({"toolkit": "harbor_board", "type": "prd", "ok": True, "count": len(board_cards)})

    gh_target = github_target_for_project(project) if status.get("github") else None
    for i, feat in enumerate(features, 1):
        title = feat.get("title", f"Feature {i}")
        body = feat.get("body", "")[:4000]
        feat_key = f"{project['id']}:feature:{i}"

        if gh_target and not find_entry("feature", feat_key, "github"):
            owner, repo = gh_target
            r = hub.create_github_issue(
                owner,
                repo,
                f"[Harbor] {title}",
                body + _harbor_footer(project),
                labels=["harbor", "feature"],
            )
            if r.success:
                upsert_entry(
                    "feature",
                    feat_key,
                    project_id=project["id"],
                    toolkit="github",
                    external_id=_extract_id(r.data, "github") or str(i),
                    external_url=_extract_url(r.data, "github"),
                    meta={"owner": owner, "repo": repo},
                )
                results.append({"toolkit": "github", "type": "feature", "ok": True, "title": title})

        if status.get("notion") and not find_entry("feature", feat_key, "notion"):
            r = hub.create_notion_page(
                title=f"[Harbor] {title}",
                content=body + _harbor_footer(project, docs_hint="docs/harbor/prd.md"),
            )
            if r.success:
                upsert_entry(
                    "feature",
                    feat_key,
                    project_id=project["id"],
                    toolkit="notion",
                    external_id="notion-page",
                    external_url="",
                )
                results.append({"toolkit": "notion", "type": "feature", "ok": True, "title": title})

    _broadcast_summary(
        project,
        f"PRD approved for **{project.get('name')}** — {len(features)} features on Harbor Board + connected tools.",
        results,
    )
    return {"project_id": project["id"], "results": results, "registry": sync_summary(project["id"])}


def sync_approve_bundle(
    project: Dict[str, Any],
    features: List[Dict[str, str]],
    prd_excerpt: str = "",
) -> Dict[str, Any]:
    return sync_prd_features(project, features, prd_excerpt=prd_excerpt)


def sync_build_job(job: Dict[str, Any], *, project: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    project = project or get_project_by_id(job.get("project_id"))
    if not project:
        return {"skipped": True}

    on_job_status(project["id"], job)

    hub = _hub()
    status = _connected()
    results: List[Dict[str, Any]] = []
    title = job.get("meta", {}).get("title") or job.get("phase", "job")
    summary = (job.get("result_summary") or "Completed")[:1500]
    msg = f"**Harbor build** `{job.get('id')}` — {title}\n\nStatus: {job.get('status')}\n\n{summary}"

    if status.get("slack") and hub.slack_delivery_ready():
        r = hub.post_slack_digest(msg)
        results.append({"toolkit": "slack", "type": "job_update", "ok": r.success})

    if status.get("discord"):
        r = hub.post_discord_message(msg[:1900])
        results.append({"toolkit": "discord", "type": "job_update", "ok": r.success})

    if status.get("gmail"):
        r = hub.sync_gmail_message(
            subject=f"[Harbor] {project.get('name')} — {title} {job.get('status')}",
            body=msg + _harbor_footer(project),
        )
        results.append({"toolkit": "gmail", "type": "gmail_sync", "ok": r.success})

    feat_key = f"{project['id']}:feature:{job.get('meta', {}).get('feature_index', '')}"
    if job.get("meta", {}).get("feature_index"):
        gh_entry = find_entry("feature", feat_key, "github")
        if gh_entry and status.get("github"):
            meta = gh_entry.get("meta", {})
            owner, repo, num = meta.get("owner"), meta.get("repo"), gh_entry.get("external_id")
            if owner and repo and num:
                r = hub.create_github_comment(owner, repo, int(num), msg)
                results.append({"toolkit": "github", "type": "comment", "ok": r.success})

    return {"results": results}


def sync_project_ecosystem(*, project_id: Optional[str] = None) -> Dict[str, Any]:
    from harbor.coding.scaffold import parse_prd_into_features, read_project_files
    from harbor.plans import list_plans

    project = get_project_by_id(project_id) if project_id else get_active_project()
    if not project:
        raise ValueError("No active project")

    out: Dict[str, Any] = {"project_id": project["id"], "synced": []}
    for plan in list_plans(project_id=project["id"]):
        out["synced"].append(sync_plan(plan, project=project))

    docs = read_project_files(project)
    prd = docs.get("files", {}).get("prd.md", "")
    if prd.strip():
        features = parse_prd_into_features(prd)
        out["synced"].append(sync_prd_features(project, features, prd_excerpt=prd[:800]))

    out["board"] = __import__("harbor.board", fromlist=["list_board"]).list_board(project["id"])
    out["registry"] = sync_summary(project["id"])
    out["connected"] = _connected()
    return out


def sync_status(*, project_id: Optional[str] = None) -> Dict[str, Any]:
    from harbor.user_settings import get_user_settings

    project = get_project_by_id(project_id) if project_id else get_active_project()
    pid = project.get("id") if project else None
    return {
        "auto_sync": get_settings().harbor_auto_sync,
        "user_settings": get_user_settings(),
        "connected": _connected(),
        "github_target": github_target_for_project(project) if project else None,
        "registry": sync_summary(pid),
        "entries": list_entries(project_id=pid),
        "board_total": __import__("harbor.board", fromlist=["list_board"]).list_board(pid).get("total", 0),
    }


def _broadcast_summary(project: Dict[str, Any], message: str, results: List[Dict[str, Any]]) -> None:
    hub = _hub()
    status = _connected()
    detail = message

    if status.get("slack") and hub.slack_delivery_ready():
        hub.post_slack_digest(detail)

    if status.get("discord"):
        hub.post_discord_message(detail[:1900])

    if status.get("gmail"):
        hub.sync_gmail_message(
            subject=f"[Harbor] {project.get('name')} — ecosystem sync",
            body=detail + _harbor_footer(project),
        )


def on_plan_created(plan: Dict[str, Any]) -> None:
    if not get_settings().harbor_auto_sync:
        return
    try:
        sync_plan(plan)
    except Exception:
        pass


def on_task_toggled(plan_id: str, task_index: int, done: bool) -> None:
    project = get_active_project()
    if not project:
        return
    col = "done" if done else "backlog"
    move_card_by_source(project["id"], "plan_task", f"{plan_id}:{task_index}", col)
