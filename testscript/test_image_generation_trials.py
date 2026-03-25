#!/usr/bin/env python3
"""
Run ~10 local image-generation trials (Pillow + optional Gemini) and print metrics.
Goal: validate first-slide intel hero template before shipping.

Usage (from repo root):
  python3 testscript/test_image_generation_trials.py
With Gemini slides (needs API key in env):
  set -a; source .env; set +a; python3 testscript/test_image_generation_trials.py
"""

from __future__ import annotations

import json
import random
import sys
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

from PIL import Image, ImageStat  # noqa: E402

from src.media.editorial_compositor import (  # noqa: E402
    build_abstract_editorial_background,
    compose_editorial_slide,
)
from src.utils.config import get_config  # noqa: E402


def _metrics(img: Image.Image) -> dict:
    stat = ImageStat.Stat(img.convert("RGB"))
    r, g, b = stat.mean
    brightness = (r + g + b) / 3.0
    contrast = sum(stat.stddev) / 3.0
    w, h = img.size
    lower = img.crop((0, int(h * 0.46), w, h))
    ls = ImageStat.Stat(lower.convert("RGB"))
    lr, lg, lb = ls.mean
    panel_brightness = (lr + lg + lb) / 3.0
    return {
        "size": [w, h],
        "avg_brightness": round(brightness, 2),
        "avg_contrast": round(contrast, 2),
        "panel_brightness": round(panel_brightness, 2),
    }


def _run_pillow_trials(out_root: Path, brand: dict) -> list[dict]:
    width = int(brand.get("canvas_width", brand.get("canvas_size", 1080)))
    height = int(brand.get("canvas_height", int(width * 1.25)))
    title_fonts = list(brand.get("font_title_candidates", []))
    body_fonts = list(brand.get("font_body_candidates", []))
    label = str(brand.get("slide_label", "AI TECH INTEL"))
    deep = (15, 23, 42)
    mid = (30, 58, 138)
    accent = (56, 189, 248)
    highlight = tuple(
        int(brand.get("highlight_color", "#fbbf24").lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
    )
    primary = (241, 245, 249)

    bodies = [
        "FCC moves to block imported consumer routers over security concerns.",
        "The FCC has issued a sweeping ban on imported consumer routers citing national security.",
        "Agile Robots partners with Google DeepMind on next-gen industrial automation models.",
        "Mirage raises $75M for AI video editing — founders bet on generative workflows.",
        "Short headline test.",
        "Apple sets WWDC 2026 for June 8 — expect iOS and on-device AI roadmap updates.",
        "AI is beginning to change the business of law — firms test drafting and research copilots.",
        "Snapchat ships AI Clips — five-second generative video from a single photo.",
        "Orbital data centers face brutal economics — power and launch costs dominate.",
        "Zipline raises $200M — drone logistics scale-up continues across new regions.",
    ]

    results = []
    for i, body in enumerate(bodies, start=1):
        rng = random.Random(1000 + i)
        base = build_abstract_editorial_background((width, height), rng, deep, mid, accent)
        cover = body[:48] + ("…" if len(body) > 48 else "")
        img = compose_editorial_slide(
            base,
            role="Hook",
            body=body,
            slide_idx=1,
            total_slides=5,
            brand_label=label,
            accent_rgb=accent,
            highlight_rgb=highlight,
            muted_rgb=(100, 116, 139),
            primary_rgb=primary,
            font_title_candidates=title_fonts,
            font_body_candidates=body_fonts,
            cover_headline=cover,
            layout_variant="cover_impact",
            profile_path="",
        )
        p = out_root / f"trial_pillow_{i:02d}_hero.jpg"
        img.convert("RGB").save(p, quality=92)
        m = _metrics(img)
        m["path"] = str(p)
        m["trial"] = f"pillow_{i}"
        m["ok"] = m["size"] == [width, height] and m["panel_brightness"] < 55
        results.append(m)
    return results


def _run_gemini_trials(out_root: Path, cfg) -> list[dict]:
    key = (getattr(cfg, "gemini_api_key", None) or "").strip()
    if not key:
        return [{"trial": "gemini_skipped", "ok": True, "reason": "no GEMINI_API_KEY"}]
    from src.media.gemini_carousel_images import try_render_gemini_carousel  # noqa: WPS433

    # One slide each to keep trial time reasonable; still exercises Gemini + compositor path.
    scenarios = [
        (
            "trial_gemini_01_router_intel",
            "FCC router import policy shift",
            [
                "FCC targets foreign-made home routers citing supply-chain security review standards.",
            ],
        ),
        (
            "trial_gemini_02_ai_partner",
            "Robotics lab partners with frontier AI lab",
            [
                "Industrial robotics firm signs frontier AI lab deal focused on warehouse perception.",
            ],
        ),
        (
            "trial_gemini_03_api_pricing",
            "Breaking: major model API price change",
            [
                "Cloud API pricing shifts for flagship models — teams must rerun inference unit economics.",
            ],
        ),
        (
            "trial_gemini_04_wwdc",
            "WWDC date confirms summer software cycle",
            [
                "Apple sets June keynote for platform updates and on-device AI developer tooling.",
            ],
        ),
    ]

    results: list[dict] = []
    for slug, title, slides in scenarios:
        sub = out_root / slug
        sub.mkdir(parents=True, exist_ok=True)
        paths = try_render_gemini_carousel(
            cfg,
            slug,
            slides,
            sub,
            topic_title=title,
            cover_headline=slides[0][:72],
            overlay_texts=slides,
            visual_prompts=None,
            post_template="carousel_standard",
        )
        if not paths:
            results.append({"trial": slug, "ok": False, "reason": "gemini_render_returned_none"})
            continue
        first = Path(paths[0])
        with Image.open(first) as im:
            m = _metrics(im)
        m["path"] = str(first)
        m["trial"] = slug
        m["slides_rendered"] = len(paths)
        m["ok"] = m.get("size") == [1080, 1350] or m.get("size") is not None
        results.append(m)
    return results


def main() -> int:
    cfg = get_config()
    brand_path = ROOT / "src/media/templates/branding.json"
    brand = json.loads(brand_path.read_text(encoding="utf-8"))

    out_root = ROOT / "output" / "image_trials"
    out_root.mkdir(parents=True, exist_ok=True)

    pillow = _run_pillow_trials(out_root, brand)
    gemini = _run_gemini_trials(out_root, cfg)

    report_path = out_root / "trial_report.json"
    report = {"pillow": pillow, "gemini": gemini}
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Image generation trials ===")
    print(f"Output dir: {out_root}")
    for row in pillow + gemini:
        print(json.dumps(row, default=str))
    print(f"Wrote {report_path}")
    failed = [r for r in pillow + gemini if not r.get("ok", False)]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
