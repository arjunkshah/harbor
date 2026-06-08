"""Ecosystem sync tests."""

import pytest


def test_sync_plan_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("HARBOR_DEMO", "1")
    monkeypatch.setattr("harbor.workspace.ROOT", tmp_path)
    monkeypatch.setattr("harbor.workspace.WORKSPACE_FILE", tmp_path / ".harbor" / "workspace.json")
    monkeypatch.setattr("harbor.sync.registry.ROOT", tmp_path)
    monkeypatch.setattr("harbor.sync.registry.REGISTRY_FILE", tmp_path / ".harbor" / "sync_registry.json")
    monkeypatch.setattr("harbor.plans.ROOT", tmp_path)
    monkeypatch.setattr("harbor.plans.PLANS_FILE", tmp_path / ".harbor" / "plans.json")

    from harbor.config import get_settings
    from harbor import workspace as ws
    from harbor.plans import create_plan
    from harbor.sync.engine import sync_plan, sync_status

    get_settings.cache_clear()

    proj = ws.create_project("Sync test")
    plan = create_plan("Launch", "Ship v1", ["Auth", "Dashboard"], project_id=proj["id"])
    st = sync_status(project_id=proj["id"])
    assert st["registry"]["total"] >= 1

    out = sync_plan(plan, project=proj)
    assert out["plan_id"] == plan["id"]


def test_sync_prd_features_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("HARBOR_DEMO", "1")
    monkeypatch.setattr("harbor.workspace.ROOT", tmp_path)
    monkeypatch.setattr("harbor.workspace.WORKSPACE_FILE", tmp_path / ".harbor" / "workspace.json")
    monkeypatch.setattr("harbor.sync.registry.ROOT", tmp_path)
    monkeypatch.setattr("harbor.sync.registry.REGISTRY_FILE", tmp_path / ".harbor" / "sync_registry.json")

    from harbor.config import get_settings
    from harbor import workspace as ws
    from harbor.sync.engine import sync_prd_features

    get_settings.cache_clear()
    proj = ws.create_project("PRD sync", repo_path=str(tmp_path / "repo"))
    (tmp_path / "repo").mkdir()
    features = [{"title": "Auth", "body": "User story", "prompt": "build auth"}]
    out = sync_prd_features(proj, features, prd_excerpt="# PRD")
    assert out["project_id"] == proj["id"]
    assert len(out["results"]) >= 1
