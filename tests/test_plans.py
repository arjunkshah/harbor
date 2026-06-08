"""Builder plans storage tests."""

import pytest


def test_create_and_toggle_plan(tmp_path, monkeypatch):
    monkeypatch.setattr("harbor.plans.ROOT", tmp_path)
    monkeypatch.setattr("harbor.plans.PLANS_FILE", tmp_path / ".harbor" / "plans.json")

    from harbor.plans import create_plan, list_plans, toggle_task

    plan = create_plan("Ship auth", "Add OAuth flow", ["Wire Composio", "Test redirect"])
    assert plan["title"] == "Ship auth"
    assert len(plan["tasks"]) == 2

    plans = list_plans()
    assert len(plans) == 1

    updated = toggle_task(plan["id"], 0)
    assert updated is not None
    assert updated["tasks"][0]["done"] is True


def test_parse_plan_from_summary(tmp_path, monkeypatch):
    monkeypatch.setattr("harbor.plans.ROOT", tmp_path)
    monkeypatch.setattr("harbor.plans.PLANS_FILE", tmp_path / ".harbor" / "plans.json")

    from harbor.plans import parse_plan_from_summary

    summary = """Launch plan

1. Fix OAuth redirect
2. Update dashboard UI
- Write docs
"""
    plan = parse_plan_from_summary(summary, "Launch week", project_id="proj1")
    assert len(plan["tasks"]) >= 2
    assert plan["project_id"] == "proj1"
