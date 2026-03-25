"""Unit tests for story brief strategist (fallback + shape)."""

from __future__ import annotations

import pytest

from src.content import story_brief as sb

POST_FIXTURE = {
    "topic": "Example Corp announces API updates",
    "slides": [
        "Example Corp published new rate limits.",
        "Developers must migrate by Q4.",
        "Enterprise tiers gain dedicated support.",
    ],
    "poster_headlines": ["API CHANGES LIVE", "MIGRATION DEADLINE", "ENTERPRISE PLUS"],
    "visual_prompts": ["Abstract API gateway.", "Calendar deadline motif.", "Server room mood."],
    "cover_headline": "API CHANGES LIVE",
    "sources": [{"title": "Wire", "url": "https://example.com/a"}],
}


def test_fallback_story_brief_shape() -> None:
    b = sb.fallback_story_brief(POST_FIXTURE)
    assert "slide_plan" in b
    assert isinstance(b["slide_plan"], list)
    assert len(b["slide_plan"]) >= 1
    first = b["slide_plan"][0]
    assert "headline" in first and "visual_hint" in first
    assert b.get("all_in_one_datapoint_1")


def test_ensure_story_brief_respects_disable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sb, "story_strategist_enabled", lambda: False)
    b = sb.ensure_story_brief(POST_FIXTURE, cfg=object())  # unused when strategist off
    assert b["slide_plan"]
