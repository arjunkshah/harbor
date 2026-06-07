"""Tests for Harbor workflows in demo mode."""

import os

import pytest


@pytest.fixture(autouse=True)
def demo_env(monkeypatch):
    monkeypatch.setenv("HARBOR_DEMO", "1")
    from harbor.config import get_settings

    get_settings.cache_clear()


def test_morning_brief_demo():
    from harbor.workflows import run_morning_brief

    out = run_morning_brief()
    assert out.result.summary
    assert out.result.memory_savings_pct >= 0
    assert len(out.result.turns) >= 1


def test_incident_commander_demo():
    from harbor.workflows import run_incident_commander

    out = run_incident_commander("API latency spike us-east")
    assert out.result.summary
    assert out.name == "incident_commander"


def test_doctor_demo():
    from harbor.doctor import run_doctor

    assert run_doctor() is True
