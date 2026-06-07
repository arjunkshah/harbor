"""Tests for run history store."""

import os

import pytest


@pytest.fixture(autouse=True)
def demo_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HARBOR_DEMO", "1")
    from harbor.config import get_settings

    get_settings.cache_clear()


def test_save_and_list_runs(monkeypatch, tmp_path):
    import harbor.store as store

    monkeypatch.setattr(store, "HARBOR_DIR", tmp_path)
    monkeypatch.setattr(store, "RUNS_FILE", tmp_path / "runs.json")

    store.save_run("morning_brief", "Test summary", 65.0, [{"tool": "SLACK_SEND_MESSAGE"}])
    runs = store.list_runs()
    assert len(runs) == 1
    assert runs[0]["summary"] == "Test summary"
    assert store.stats()["total_runs"] == 1
