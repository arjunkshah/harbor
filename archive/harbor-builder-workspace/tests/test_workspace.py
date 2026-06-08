"""Workspace and integration choice tests."""

import pytest


def test_set_enabled_toolkits(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("COMPOSIO_TOOLKITS=github,slack\nHARBOR_DEMO=1\n")
    monkeypatch.setenv("HARBOR_DEMO", "1")
    import harbor.setup as setup_mod
    import harbor.workspace as ws

    monkeypatch.setattr(setup_mod, "ENV_FILE", env)
    monkeypatch.setattr(ws, "ROOT", tmp_path)
    monkeypatch.setattr(ws, "WORKSPACE_FILE", tmp_path / ".harbor" / "workspace.json")

    enabled = ws.set_enabled_toolkits(["github", "gmail"])
    assert enabled == ["github", "gmail"]
    assert "github,gmail" in env.read_text()


def test_project_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr("harbor.workspace.ROOT", tmp_path)
    monkeypatch.setattr("harbor.workspace.WORKSPACE_FILE", tmp_path / ".harbor" / "workspace.json")

    from harbor import workspace as ws

    p = ws.create_project("Ship v1", focus="agents", company="Acme")
    assert p["name"] == "Ship v1"
    active = ws.get_active_project()
    assert active["id"] == p["id"]
    ws.bump_project_run(p["id"])
    active2 = ws.get_active_project()
    assert active2["run_count"] == 1


def test_integration_catalog_enabled_filter(monkeypatch):
    monkeypatch.setenv("COMPOSIO_TOOLKITS", "github")
    monkeypatch.setenv("HARBOR_DEMO", "1")
    from harbor.config import get_settings
    from harbor.workspace import integration_catalog

    get_settings.cache_clear()
    rows = integration_catalog(connected={"github": True, "slack": False})
    gh = next(r for r in rows if r["slug"] == "github")
    sl = next(r for r in rows if r["slug"] == "slack")
    assert gh["enabled"] is True
    assert sl["enabled"] is False
