"""
Carousel image generator (product path).

`carousel_standard` uses Gemini plus a compositor layer. See `IMAGE_RENDER_MODE`:
  - cinematic_overlay (default): text-free cinematic background + bold PIL headline band.
  - arxiv_integrated: 3D isometric frames with headline baked into the image model.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import List, Optional, Sequence

from PIL import Image

from src.media.editorial_compositor import build_abstract_editorial_background, compose_editorial_slide
from src.utils.config import get_config


def save_rgb_jpeg_under_limit(
    img: Image.Image,
    out_path: Path,
    *,
    max_bytes: int,
    start_quality: int = 95,
    min_quality: int = 55,
    quality_step: int = 5,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = Path(out_path)

    rgb = img.convert("RGB")
    q = start_quality
    while True:
        rgb.save(out_path, format="JPEG", quality=q, optimize=True)
        size = out_path.stat().st_size
        if size <= max_bytes or q <= min_quality:
            return
        q = max(min_quality, q - quality_step)


class CarouselImageGenerator:
    """
    Production-facing carousel renderer.

    Bytecode version exists in `__pycache__`. This override routes `carousel_standard`
    through `src.media.gemini_carousel_images.try_render_gemini_carousel`.
    """

    def __init__(self, template_path: Path | None = None) -> None:
        self._template_path = template_path or Path(__file__).resolve().parent / "templates"
        brand_path = self._template_path / "branding.json"
        self._brand = json.loads(brand_path.read_text(encoding="utf-8"))

    def _hex_to_rgb(self, hex_str: str) -> tuple[int, int, int]:
        s = (hex_str or "").strip().lower()
        if s.startswith("#"):
            s = s[1:]
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) != 6:
            # Best-effort fallback to cyan-ish
            return (56, 189, 248)
        return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[misc]

    def render_topic_slides(
        self,
        topic_slug: str,
        slide_texts: List[str],
        out_dir: Path,
        *,
        topic_title: str = "",
        cover_headline: str = "",
        overlay_texts: List[str] | None = None,
        visual_prompts: List[str] | None = None,
        post_template: str = "carousel_standard",
    ) -> List[Path]:
        cfg = get_config()
        slides = list(overlay_texts if overlay_texts is not None else slide_texts)
        if not slides:
            return []

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Preferred path: Gemini renders with integrated typography.
        if post_template == "carousel_standard":
            try:
                from src.media.gemini_carousel_images import try_render_gemini_carousel

                paths = try_render_gemini_carousel(
                    cfg,
                    topic_slug,
                    slide_texts,
                    out_dir,
                    topic_title=topic_title,
                    cover_headline=cover_headline or slides[0][:72],
                    overlay_texts=slides,
                    visual_prompts=visual_prompts,
                    post_template=post_template,
                )
                if paths:
                    return [Path(p) for p in paths]
            except Exception:
                # Fall back to Pillow for resilience; we'll still pass the pipeline.
                pass

        # Fallback path (Pillow): abstract background + editorial compositor overlays.
        width = int(self._brand.get("canvas_width", 1080))
        height = int(self._brand.get("canvas_height", int(width * 1.25)))
        deep = (15, 23, 42)
        mid = (30, 58, 138)

        accent_rgb = self._hex_to_rgb(str(self._brand.get("accent", "#38bdf8")))
        highlight_rgb = self._hex_to_rgb(str(self._brand.get("highlight_color", "#fbbf24")))
        primary_rgb = self._hex_to_rgb(str(self._brand.get("primary_text", "#f1f5f9")))
        muted_rgb = self._hex_to_rgb(str(self._brand.get("muted", "#64748b")))

        title_fonts = list(self._brand.get("font_title_candidates", []))
        body_fonts = list(self._brand.get("font_body_candidates", []))
        label = str(self._brand.get("slide_label", "ARXIV INTEL"))

        roles = list(self._brand.get("slide_role_labels", []))
        total = len(slides)

        max_bytes = int(self._brand.get("max_jpeg_bytes", 8_388_608))
        paths: List[Path] = []

        for i, body in enumerate(slides, start=1):
            rng = random.Random(1000 + i)
            base = build_abstract_editorial_background(
                (width, height),
                rng,
                deep,
                mid,
                accent_rgb,
            )

            role = roles[i - 1] if i - 1 < len(roles) else f"Slide {i}"
            layout_variant = "cover_impact" if i == 1 else "left_dock"
            img = compose_editorial_slide(
                base,
                role=role,
                body=body,
                slide_idx=i,
                total_slides=total,
                brand_label=label,
                accent_rgb=accent_rgb,
                highlight_rgb=highlight_rgb,
                muted_rgb=muted_rgb,
                primary_rgb=primary_rgb,
                font_title_candidates=title_fonts,
                font_body_candidates=body_fonts,
                topic_kicker=topic_title[:80] if topic_title else "",
                cover_headline=cover_headline if i == 1 else "",
                layout_variant=layout_variant,
                profile_path="",
            )

            out_path = out_dir / f"slide_{i:02d}.jpg"
            save_rgb_jpeg_under_limit(img, out_path, max_bytes=max_bytes)
            paths.append(out_path)

        return paths

