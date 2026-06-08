"""Tests for indie-hacker integration defaults."""

import pytest


def test_solo_default_toolkits_exclude_slack():
    from harbor.integrations import SOLO_DEFAULT_TOOLKITS

    assert "github" in SOLO_DEFAULT_TOOLKITS
    assert "slack" not in SOLO_DEFAULT_TOOLKITS


def test_composio_toolkits_env_parsing(monkeypatch):
    monkeypatch.setenv("COMPOSIO_TOOLKITS", "github, linear ,gmail")
    monkeypatch.setenv("HARBOR_DEMO", "1")
    from harbor.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    assert s.active_toolkits() == ["github", "linear", "gmail"]


def test_morning_brief_instructions_without_slack():
    from harbor.integrations import morning_brief_instructions

    text = morning_brief_instructions(
        connected={"github": True, "linear": False, "gmail": False, "slack": False},
        slack_ready=False,
    )
    assert "terminal" in text.lower()
    assert "SLACK" not in text


def test_morning_brief_instructions_with_slack():
    from harbor.integrations import morning_brief_instructions

    text = morning_brief_instructions(
        connected={"github": True, "linear": True, "gmail": True, "slack": True},
        slack_ready=True,
    )
    assert "SLACK_SEND_MESSAGE" in text
