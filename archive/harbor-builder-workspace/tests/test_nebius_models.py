"""Nebius model migration tests."""

from harbor.nebius_models import (
    DEFAULT_NEBIUS_MODEL,
    is_deprecated_nebius_model,
    normalize_nebius_model,
)


def test_normalize_deprecated_kimi():
    assert normalize_nebius_model("moonshotai/Kimi-K2-Instruct-0905") == DEFAULT_NEBIUS_MODEL
    assert is_deprecated_nebius_model("moonshotai/Kimi-K2-Instruct-0905")


def test_normalize_keeps_current():
    assert normalize_nebius_model("moonshotai/Kimi-K2.5") == "moonshotai/Kimi-K2.5"
    assert normalize_nebius_model("") == DEFAULT_NEBIUS_MODEL
