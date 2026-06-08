"""Tests for Tavily demo client."""

import os


def test_tavily_demo_search():
    os.environ["HARBOR_DEMO"] = "1"
    from harbor.config import get_settings

    get_settings.cache_clear()
    from harbor.tavily import get_tavily

    t = get_tavily()
    bundle = t.search_and_answer("OpenClaw agents")
    assert bundle.hits
    assert bundle.to_context_block()
