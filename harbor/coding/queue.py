"""Coding job queue — queue prompts, run Codex/Claude, monitor."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from harbor.coding.backends import resolve_agent, run_agent_process
from harbor.coding.notify import push_alert
from harbor.coding.scaffold import project_workdir
from harbor.config import get_settings

ROOT = Path(__file__).resolve().parent.parent.parent
QUEUE_FILE = ROOT / ".harbor" / "coding_queue.json"
LOGS_DIR = ROOT / ".harbor" / "coding_logs"


@dataclass
class CodingJob:
    id: str
    project_id: str
    project_name: str
    agent: str
    prompt: str
    phase: str  # docs | implement | review | custom
    status: str  # queued | running | needs_input | completed | failed
    created_at: str
    started_at: str = ""
    completed_at: str = ""
    log_path: str = ""
    pid: Optional[int] = None
    result_summary: str = ""
    needs_attention: bool = False
    attention_reason: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    (ROOT / ".harbor").mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> List[CodingJob]:
    _ensure()
    if not QUEUE_FILE.exists():
        return []
    try:
        raw = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        return [CodingJob(**item) for item in raw]
    except (json.JSONDecodeError, TypeError):
        return []


def _save(jobs: List[CodingJob]) -> None:
    _ensure()
    QUEUE_FILE.write_text(
        json.dumps([j.to_dict() for j in jobs[:80]], indent=2),
        encoding="utf-8",
    )


def list_jobs(
    *,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    jobs = _load()
    if project_id:
        jobs = [j for j in jobs if j.project_id == project_id]
    if status:
        jobs = [j for j in jobs if j.status == status]
    return [j.to_dict() for j in jobs[:limit]]


def enqueue_job(
    project: Dict[str, Any],
    prompt: str,
    *,
    phase: str = "implement",
    agent: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())[:8]
    log_path = LOGS_DIR / f"{job_id}.log"
    chosen = resolve_agent(agent or project.get("coding_agent"))
    job = CodingJob(
        id=job_id,
        project_id=project["id"],
        project_name=project.get("name", "project"),
        agent=chosen,
        prompt=prompt.strip(),
        phase=phase,
        status="queued",
        created_at=_now(),
        log_path=str(log_path),
        meta=meta or {},
    )
    jobs = _load()
    jobs.insert(0, job)
    _save(jobs)
    return job.to_dict()


def enqueue_batch(project: Dict[str, Any], prompts: List[Dict[str, str]], *, agent: Optional[str] = None) -> List[Dict[str, Any]]:
    out = []
    for item in prompts:
        out.append(
            enqueue_job(
                project,
                item["prompt"],
                phase=item.get("phase", "implement"),
                agent=agent,
                meta={"title": item.get("title", "")},
            )
        )
    return out


def _poll_running(job: CodingJob, proc) -> CodingJob:
    rc = proc.poll()
    if rc is None:
        return job
    job.completed_at = _now()
    job.pid = None
    log_tail = ""
    try:
        log_tail = Path(job.log_path).read_text(encoding="utf-8")[-1500:]
    except Exception:
        pass
    if rc == 0:
        job.status = "completed"
        job.result_summary = log_tail[-400:] or "Completed successfully"
        push_alert(
            f"{job.project_name}: {job.phase} done",
            job.meta.get("title") or job.prompt[:120],
            project_id=job.project_id,
            job_id=job.id,
        )
    else:
        job.status = "failed"
        job.needs_attention = True
        job.attention_reason = f"Exit code {rc}"
        job.result_summary = log_tail[-400:] or f"Failed with code {rc}"
        push_alert(
            f"{job.project_name}: needs you",
            job.attention_reason,
            level="warn",
            project_id=job.project_id,
            job_id=job.id,
            needs_you=True,
        )
    return job


def tick_worker() -> Optional[Dict[str, Any]]:
    """Non-blocking: poll running PIDs, start next queued job."""
    import os

    settings = get_settings()
    jobs = _load()
    changed = False

    for i, job in enumerate(jobs):
        if job.status != "running" or not job.pid:
            continue
        try:
            os.kill(job.pid, 0)
        except ProcessLookupError:
            job = _finish_job_from_log(job)
            jobs[i] = job
            changed = True
            _maybe_chain_review(jobs, job)
        except PermissionError:
            pass

    if changed:
        _save(jobs)

    if any(j.status == "running" for j in jobs):
        return next(j.to_dict() for j in jobs if j.status == "running")

    for i, job in enumerate(jobs):
        if job.status != "queued":
            continue
        from harbor.workspace import get_project_by_id, set_build_phase

        project = get_project_by_id(job.project_id) or {
            "id": job.project_id,
            "name": job.project_name,
        }
        workdir = project_workdir(project)
        workdir.mkdir(parents=True, exist_ok=True)
        demo = settings.demo_mode or job.agent == "demo"
        if demo:
            job.agent = "demo"
        try:
            proc = run_agent_process(
                job.agent,
                job.prompt,
                workdir=workdir,
                log_path=Path(job.log_path),
                demo_mode=demo,
            )
            job.status = "running"
            job.started_at = _now()
            job.pid = proc.pid
            jobs[i] = job
            _save(jobs)
            set_build_phase(job.project_id, "building")
            return job.to_dict()
        except Exception as exc:
            job.status = "failed"
            job.needs_attention = True
            job.attention_reason = str(exc)
            jobs[i] = job
            _save(jobs)
            push_alert(
                f"{job.project_name}: failed to start",
                str(exc),
                level="warn",
                project_id=job.project_id,
                job_id=job.id,
                needs_you=True,
            )
            return job.to_dict()

    return None


def _finish_job_from_log(job: CodingJob) -> CodingJob:
    job.completed_at = _now()
    job.pid = None
    log_tail = ""
    try:
        log_tail = Path(job.log_path).read_text(encoding="utf-8")
    except Exception:
        pass
    if "[demo] completed" in log_tail or "SHIP READY" in log_tail.upper():
        job.status = "completed"
        job.result_summary = log_tail[-400:] or "Completed"
        push_alert(
            f"{job.project_name}: {job.phase} done",
            job.meta.get("title") or job.prompt[:120],
            project_id=job.project_id,
            job_id=job.id,
        )
        if job.phase == "review" and "SHIP READY" in log_tail.upper():
            from harbor.workspace import set_build_phase

            set_build_phase(job.project_id, "done")
    elif "error" in log_tail.lower()[-500:] or "failed" in log_tail.lower()[-300:]:
        job.status = "failed"
        job.needs_attention = True
        job.attention_reason = "Agent reported failure — check log"
        job.result_summary = log_tail[-400:]
        push_alert(
            f"{job.project_name}: needs you",
            job.attention_reason,
            level="warn",
            project_id=job.project_id,
            job_id=job.id,
            needs_you=True,
        )
    else:
        job.status = "completed"
        job.result_summary = log_tail[-400:] or "Completed"
        push_alert(
            f"{job.project_name}: {job.phase} done",
            job.meta.get("title") or "Coding job finished",
            project_id=job.project_id,
            job_id=job.id,
        )
    return job


def _maybe_chain_review(jobs: List[CodingJob], finished: CodingJob) -> None:
    """After all implement jobs complete, queue a review pass."""
    if finished.status != "completed" or finished.phase != "implement":
        return
    project_jobs = [j for j in jobs if j.project_id == finished.project_id]
    pending = [j for j in project_jobs if j.status in ("queued", "running") and j.phase == "implement"]
    if pending:
        return
    if any(j.phase == "review" for j in project_jobs):
        return
    from harbor.workspace import get_project_by_id, set_build_phase

    project = get_project_by_id(finished.project_id)
    if not project:
        return
    review_prompt = (
        "Review the implementation against docs/harbor/prd.md. "
        "List gaps, bugs, and a short next-iteration prompt if work remains. "
        "If complete, say SHIP READY."
    )
    enqueue_job(project, review_prompt, phase="review", agent=finished.agent)
    set_build_phase(finished.project_id, "review")


def queue_stats() -> Dict[str, Any]:
    jobs = _load()
    return {
        "queued": sum(1 for j in jobs if j.status == "queued"),
        "running": sum(1 for j in jobs if j.status == "running"),
        "needs_you": sum(1 for j in jobs if j.needs_attention or j.status == "needs_input"),
        "completed": sum(1 for j in jobs if j.status == "completed"),
        "failed": sum(1 for j in jobs if j.status == "failed"),
    }
