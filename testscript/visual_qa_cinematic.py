#!/usr/bin/env python3
"""
Visual QA for the cinematic news template (PIL compositor with or without Gemini).

Writes frames under output/visual_qa/<timestamp>/:
  - slide_01.jpg …
  - _meta/… (prompts when Gemini ran)
  - manifest.json (headlines + mode)

Usage (repo root):
  python3 testscript/visual_qa_cinematic.py              # compositor-only smoke (no API)
  IMAGE_RENDER_MODE=cinematic_overlay python3 testscript/visual_qa_cinematic.py --gemini
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from main import _PycRecoveryFinder  # noqa: E402

sys.meta_path.insert(0, _PycRecoveryFinder(ROOT))

from src.media.editorial_compositor import (  # noqa: E402
    build_abstract_editorial_background,
    compose_cinematic_news_slide,
)
from src.media.image_generator import CarouselImageGenerator, save_rgb_jpeg_under_limit  # noqa: E402
from src.utils.config import get_config  # noqa: E402


def _compositor_only(out_dir: Path, brand: dict) -> list[dict]:
    width = int(brand.get("canvas_width", 1080))
    height = int(brand.get("canvas_height", int(width * 1.25)))
    deep = _tuple_from_hex(brand.get("background", "#0f172a"))
    mid = (30, 58, 138)
    accent = _tuple_from_hex(brand.get("accent", "#38bdf8"))

    rng = random.Random(42)
    base = build_abstract_editorial_background((width, height), rng, deep, mid, accent)

    highlights = [
        "AMAZON EYES SMARTPHONE COMEBACK AS RIVALS DIG IN",
        "FCC MOVES ON FOREIGN ROUTERS OVER SUPPLY CHAIN RISK",
        "ZOOX ROBOTAXIS EXPAND TO NEW U S CITIES",
    ]
    title_fonts = list(brand.get("font_title_candidates", []))
    body_fonts = list(brand.get("font_body_candidates", []))
    highlight_rgb = _tuple_from_hex(brand.get("highlight_color", "#fbbf24"))
    primary_rgb = _tuple_from_hex(brand.get("primary_text", "#f1f5f9"))
    accent_rgb = accent
    handle = str(brand.get("instagram_handle", ""))
    logo_path = str(brand.get("logo_path", ""))

    rows: list[dict] = []
    for i, hl in enumerate(highlights, start=1):
        img = compose_cinematic_news_slide(
            base,
            headline=hl,
            font_title_candidates=title_fonts,
            font_body_candidates=body_fonts,
            highlight_rgb=highlight_rgb,
            primary_rgb=primary_rgb,
            accent_rgb=accent_rgb,
            handle=handle,
            logo_path=logo_path,
        )
        p = out_dir / f"slide_{i:02d}.jpg"
        save_rgb_jpeg_under_limit(img, p, max_bytes=int(brand.get("max_jpeg_bytes", 8_388_608)))
        rows.append({"slide": i, "headline": hl, "path": str(p)})
    return rows


def _tuple_from_hex(hex_str: str) -> tuple[int, int, int]:
    s = (hex_str or "").strip().lower().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return (15, 23, 42)
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[misc]


def _gemini_path(out_dir: Path) -> list[dict]:
    from src.media.gemini_carousel_images import try_render_gemini_carousel

    cfg = get_config()
    paths = try_render_gemini_carousel(
        cfg,
        "visual_qa_gemini",
        [
            "TRIAL ONE LINE HEADLINE FOR COMPOSITOR QA",
            "SECOND SLIDE SUPPORTING DETAIL LINE GOES HERE",
        ],
        out_dir,
        topic_title="Visual QA synthetic topic",
        cover_headline="TRIAL ONE LINE HEADLINE FOR COMPOSITOR QA",
        overlay_texts=None,
        visual_prompts=[
            "Futuristic city skyline at blue hour, subtle autonomous vehicle light trails, no logos.",
            "Clean minimalist server corridor with cyan edge lighting, shallow depth of field.",
        ],
    )
    if not paths:
        return []
    return [{"slide": i + 1, "path": p, "headline": ""} for i, p in enumerate(paths)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini", action="store_true", help="Call Gemini image model (needs API key)")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "output" / "visual_qa" / ts
    out.mkdir(parents=True, exist_ok=True)

    gen = CarouselImageGenerator()
    brand = gen._brand  # noqa: SLF001

    if args.gemini:
        rows = _gemini_path(out)
        mode = "gemini"
    else:
        rows = _compositor_only(out, brand)
        mode = "compositor_only"

    manifest = {
        "created_utc": ts,
        "mode": mode,
        "image_render_mode": __import__("os").environ.get("IMAGE_RENDER_MODE", "cinematic_overlay"),
        "slides": rows,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("Wrote under", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
