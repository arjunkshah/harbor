"""Coding pipeline tests."""

import pytest


def test_scaffold_and_queue_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("HARBOR_DEMO", "1")
    monkeypatch.setattr("harbor.workspace.ROOT", tmp_path)
    monkeypatch.setattr("harbor.workspace.WORKSPACE_FILE", tmp_path / ".harbor" / "workspace.json")
    monkeypatch.setattr("harbor.coding.scaffold.ROOT", tmp_path)
    monkeypatch.setattr("harbor.coding.queue.ROOT", tmp_path)
    monkeypatch.setattr("harbor.coding.queue.QUEUE_FILE", tmp_path / ".harbor" / "coding_queue.json")
    monkeypatch.setattr("harbor.coding.queue.LOGS_DIR", tmp_path / ".harbor" / "coding_logs")
    monkeypatch.setattr("harbor.coding.notify.ROOT", tmp_path)
    monkeypatch.setattr("harbor.coding.notify.ALERTS_FILE", tmp_path / ".harbor" / "alerts.json")

    from harbor.config import get_settings
    from harbor import workspace as ws
    from harbor.coding.scaffold import write_ideation, write_prd, parse_prd_into_features, materialize_features
    from harbor.coding.queue import enqueue_job, tick_worker, list_jobs

    get_settings.cache_clear()

    proj = ws.create_project("Test app", repo_path=str(tmp_path / "repo"))
    (tmp_path / "repo").mkdir()

    write_ideation(proj, "Build a todo API with auth")
    write_prd(proj, "### Feature: Auth\n- story\n\n### Feature: API\n- story")
    features = parse_prd_into_features("### Feature: Auth\n\n### Feature: API\n")
    assert len(features) >= 1
    materialize_features(proj, features)

    job = enqueue_job(proj, "implement auth module", phase="implement")
    assert job["status"] == "queued"

    import time

    tick_worker()
    time.sleep(3)
    tick_worker()

    jobs = list_jobs(project_id=proj["id"])
    assert any(j["status"] in ("running", "completed") for j in jobs)


def test_detect_agents():
    from harbor.coding.backends import detect_coding_agents

    agents = detect_coding_agents()
    assert any(a.id == "codex" for a in agents)
