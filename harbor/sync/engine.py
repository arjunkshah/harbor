"""Push Harbor plans, PRDs, and build state into connected Composio apps."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

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
    lines = [
        "",
        "---",
        f"*Synced from Harbor · project `{project.get('name', '')}`*",
    ]
    if docs_hint:
        lines.append(f"Docs: `{docs_hint}`")
    return "\n".join(lines)


def _extract_url(data: Any, toolkit: str) -> str:
    if not isinstance(data, dict):
        return ""
    if toolkit == "linear":
        return str(data.get("url") or data.get("issueUrl") or data.get("data", {}).get("url", ""))
    if toolkit == "github":
        return str(data.get("html_url") or data.get("url") or "")
    return ""


def _extract_id(data: Any, toolkit: str) -> str:
    if not isinstance(data, dict):
        return ""
    if toolkit == "linear":
        return str(data.get("id") or data.get("issueId") or data.get("data", {}).get("id", ""))
    if toolkit == "github":
        return str(data.get("number") or data.get("id") or "")
    return ""


def sync_plan(plan: Dict[str, Any], *, project: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sync plan + tasks to Linear issues and GitHub issues."""
    project = project or (get_project_by_id(plan.get("project_id")) if plan.get("project_id") else get_active_project())
    if not project:
        raise ValueError("No project for plan sync")

    hub = _hub()
    status = _connected()
    results: List[Dict[str, Any]] = []
    gh_target = github_target_for_project(project) if status.get("github") else None

    parent_desc = f"{plan.get('goal', '')}\n\nHarbor plan `{plan.get('id')}`"
    if status.get("linear"):
        parent_key = f"plan:{plan['id']}"
        if not find_entry("plan", parent_key, "linear"):
            r = hub.create_linear_issue(f"[Harbor] {plan.get('title', 'Plan')}", parent_desc)
            if r.success:
                upsert_entry(
                    "plan",
                    parent_key,
                    project_id=project["id"],
                    toolkit="linear",
                    external_id=_extract_id(r.data, "linear") or "linear-plan",
                    external_url=_extract_url(r.data, "linear"),
                )
                results.append({"toolkit": "linear", "type": "plan", "ok": True, "title": plan.get("title")})

    for i, task in enumerate(plan.get("tasks", [])):
        text = task.get("text", "") if isinstance(task, dict) else str(task)
        if not text:
            continue
        task_key = f"{plan['id']}:{i}"

        if status.get("linear") and not find_entry("plan_task", task_key, "linear"):
            body = f"Plan task from Harbor\n\n- Plan: {plan.get('title')}\n- Done: {task.get('done', False) if isinstance(task, dict) else False}{_harbor_footer(project)}"
            r = hub.create_linear_issue(f"[Harbor] {text[:120]}", body)
            if r.success:
                upsert_entry(
                    "plan_task",
                    task_key,
                    project_id=project["id"],
                    toolkit="linear",
                    external_id=_extract_id(r.data, "linear") or f"linear-task-{i}",
                    external_url=_extract_url(r.data, "linear"),
                )
                results.append({"toolkit": "linear", "type": "plan_task", "ok": True, "title": text[:80]})

        if gh_target and not find_entry("plan_task", task_key, "github"):
            owner, repo = gh_target
            body = f"Harbor plan task\n\nPlan: **{plan.get('title')}**\n\n{text}{_harbor_footer(project, docs_hint='docs/harbor/')}"
            r = hub.create_github_issue(owner, repo, text[:120], body, labels=["harbor"])
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
        f"Plan synced: **{plan.get('title')}** — {len(plan.get('tasks', []))} tasks pushed to your connected tools.",
        results,
    )
    return {"plan_id": plan["id"], "results": results, "registry": sync_summary(project["id"])}


def sync_prd_features(
    project: Dict[str, Any],
    features: List[Dict[str, str]],
    *,
    prd_excerpt: str = "",
) -> Dict[str, Any]:
    """Sync PRD features to Linear + GitHub after approve."""
    hub = _hub()
    status = _connected()
    results: List[Dict[str, Any]] = []
    gh_target = github_target_for_project(project) if status.get("github") else None

    if status.get("linear"):
        parent_key = f"prd:{project['id']}"
        if not find_entry("prd", parent_key, "linear"):
            r = hub.create_linear_issue(
                f"[Harbor PRD] {project.get('name', 'Project')}",
                (prd_excerpt or "PRD approved in Harbor") + _harbor_footer(project, docs_hint="docs/harbor/prd.md"),
            )
            if r.success:
                upsert_entry(
                    "prd",
                    parent_key,
                    project_id=project["id"],
                    toolkit="linear",
                    external_id=_extract_id(r.data, "linear") or "prd-parent",
                    external_url=_extract_url(r.data, "linear"),
                )
                results.append({"toolkit": "linear", "type": "prd", "ok": True})

    for i, feat in enumerate(features, 1):
        title = feat.get("title", f"Feature {i}")
        body = feat.get("body", "")[:4000]
        feat_key = f"{project['id']}:feature:{i}"

        if status.get("linear") and not find_entry("feature", feat_key, "linear"):
            r = hub.create_linear_issue(
                f"[Harbor] {title}",
                body + _harbor_footer(project, docs_hint="docs/harbor/features/"),
            )
            if r.success:
                upsert_entry(
                    "feature",
                    feat_key,
                    project_id=project["id"],
                    toolkit="linear",
                    external_id=_extract_id(r.data, "linear") or f"feat-{i}",
                    external_url=_extract_url(r.data, "linear"),
                )
                results.append({"toolkit": "linear", "type": "feature", "ok": True, "title": title})

        if gh_target and not find_entry("feature", feat_key, "github"):
            owner, repo = gh_target
            r = hub.create_github_issue(owner, repo, f"[Harbor] {title}", body + _harbor_footer(project), labels=["harbor", "feature"])
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

    _broadcast_summary(
        project,
        f"PRD approved for **{project.get('name')}** — {len(features)} features synced. Coding jobs queued in Harbor.",
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
    """On coding job complete — comment on linked issues + notify."""
    project = project or get_project_by_id(job.get("project_id"))
    if not project:
        return {"skipped": True}

    hub = _hub()
    status = _connected()
    results: List[Dict[str, Any]] = []
    title = job.get("meta", {}).get("title") or job.get("phase", "job")
    summary = (job.get("result_summary") or "Completed")[:1500]
    msg = f"**Harbor build job** `{job.get('id')}` — {title}\n\nStatus: {job.get('status')}\n\n{summary}"

    if status.get("slack") and hub.slack_delivery_ready():
        r = hub.post_slack_digest(msg)
        results.append({"toolkit": "slack", "type": "job_update", "ok": r.success})

    if status.get("gmail"):
        r = hub.create_gmail_draft(
            subject=f"[Harbor] {project.get('name')} — {title} {job.get('status')}",
            body=msg + _harbor_footer(project),
        )
        if r.success:
            results.append({"toolkit": "gmail", "type": "job_draft", "ok": True})

    feat_key = f"{project['id']}:feature:{job.get('meta', {}).get('feature_index', '')}"
    if not job.get("meta", {}).get("feature_index"):
        return {"results": results}

    gh_entry = find_entry("feature", feat_key, "github")
    if gh_entry and status.get("github"):
        meta = gh_entry.get("meta", {})
        owner, repo = meta.get("owner"), meta.get("repo")
        num = gh_entry.get("external_id")
        if owner and repo and num:
            r = hub.create_github_comment(owner, repo, int(num), msg)
            results.append({"toolkit": "github", "type": "comment", "ok": r.success})

    return {"results": results}


def sync_project_ecosystem(*, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Full re-sync: all plans + PRD features for active project."""
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

    out["registry"] = sync_summary(project["id"])
    out["connected"] = _connected()
    return out


def sync_status(*, project_id: Optional[str] = None) -> Dict[str, Any]:
    project = get_project_by_id(project_id) if project_id else get_active_project()
    pid = project.get("id") if project else None
    s = get_settings()
    return {
        "auto_sync": s.harbor_auto_sync,
        "connected": _connected(),
        "github_target": github_target_for_project(project) if project else None,
        "registry": sync_summary(pid),
        "entries": list_entries(project_id=pid),
    }


def _broadcast_summary(project: Dict[str, Any], message: str, results: List[Dict[str, Any]]) -> None:
    hub = _hub()
    status = _connected()
    links = [r for r in results if r.get("ok") and r.get("title")]
    detail = message
    if links:
        detail += "\n\n" + "\n".join(f"• {r.get('toolkit')}: {r.get('title', r.get('type'))}" for r in links[:8])

    if status.get("slack") and hub.slack_delivery_ready():
        hub.post_slack_digest(detail)

    if status.get("gmail"):
        hub.create_gmail_draft(
            subject=f"[Harbor] {project.get('name')} — ecosystem sync",
            body=detail + _harbor_footer(project),
        )


def on_plan_created(plan: Dict[str, Any]) -> None:
    s = get_settings()
    if not s.harbor_auto_sync:
        return
    try:
        sync_plan(plan)
    except Exception:
        pass


def on_task_toggled(plan_id: str, task_index: int, done: bool) -> None:
    s = get_settings()
    if not s.harbor_auto_sync:
        return
    hub = _hub()
    if not _connected().get("linear"):
        return
    entry = find_entry("plan_task", f"{plan_id}:{task_index}", "linear")
    if not entry:
        return
    try:
        hub.update_linear_issue(
            entry["external_id"],
            description=f"Task {'completed' if done else 'reopened'} via Harbor dashboard.",
        )
    except Exception:
        pass
