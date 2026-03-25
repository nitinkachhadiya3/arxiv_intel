"""Smoke tests for cinematic compositor helpers (no Gemini)."""

from __future__ import annotations

from PIL import Image

from src.media.editorial_compositor import compose_cinematic_blueprint_slide, compose_cinematic_news_slide


def _brand_font_lists() -> tuple[list[str], list[str]]:
    # Empty lists fall back to default font in compositor.
    return [], []


def test_compose_cinematic_news_slide_with_sublines() -> None:
    base = Image.new("RGB", (640, 800), color=(40, 44, 80))
    titles, bodies = _brand_font_lists()
    img = compose_cinematic_news_slide(
        base,
        headline="MAJOR PLATFORM UPDATE",
        font_title_candidates=titles,
        font_body_candidates=bodies,
        highlight_rgb=(251, 191, 36),
        primary_rgb=(241, 245, 249),
        accent_rgb=(56, 189, 248),
        handle="@test_intel",
        sublines=["► Fact one for feed skim", "► Fact two"],
    )
    assert img.size == base.size
    assert img.mode == "RGB"


def test_compose_cinematic_blueprint_slide() -> None:
    base = Image.new("RGB", (640, 800), color=(30, 32, 60))
    titles, bodies = _brand_font_lists()
    img = compose_cinematic_blueprint_slide(
        base,
        headline="DETAIL HEADLINE",
        detail_lines=["Supporting sentence one.", "Supporting sentence two."],
        font_title_candidates=titles,
        font_body_candidates=bodies,
        highlight_rgb=(251, 191, 36),
        primary_rgb=(241, 245, 249),
        accent_rgb=(56, 189, 248),
        slide_label="ARXIV INTEL · 2/4",
    )
    assert img.size == base.size
