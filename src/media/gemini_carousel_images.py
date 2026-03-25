"""
Gemini carousel frames: ArXiv Intel 3D isometric scenes with headline text baked into the render.

No PIL caption plates or grey/black lower-third bars — only optional thin border + canvas fit.
"""

from __future__ import annotations

import io
import os
import re
import time
from pathlib import Path
from typing import List, Optional, Sequence

from google import genai
from google.genai import types
from PIL import Image, ImageOps

from src.media.editorial_compositor import compose_editorial_slide
from src.media.image_generator import CarouselImageGenerator, save_rgb_jpeg_under_limit
from src.utils.config import AppConfig
from src.utils.gemini_models import gemini_image_model_candidates, is_gemini_model_unavailable_error
from src.utils.logger import get_logger, log_stage

_LOG = get_logger("media.gemini_carousel")

# Gemini Image API aspect ratios (4:5 is not listed — use 3:4 or 2:3 for portrait).
_SUPPORTED_ASPECT = frozenset({"1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9"})


def _normalize_headline(text: str, max_len: int = 160) -> str:
    s = " ".join((text or "").split()).strip()
    if len(s) <= max_len:
        return s
    cut = s[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or s[:max_len]) + "…"


def _aspect_ratio_for_request(cfg: AppConfig) -> str:
    """Portrait-first: bytecode AppConfig often defaults to 1:1; carousels need tall feed assets."""
    env_ar = (os.getenv("GEMINI_IMAGE_ASPECT_RATIO") or "").strip()
    cfg_ar = str(getattr(cfg, "gemini_image_aspect_ratio", "") or "").strip()
    raw = env_ar or (cfg_ar if cfg_ar and cfg_ar != "1:1" else "") or "3:4"
    ar = str(raw).strip()
    if ar == "4:5":
        return "3:4"
    if ar in _SUPPORTED_ASPECT:
        return ar
    return "3:4"


def _image_size_for_request(cfg: AppConfig) -> str | None:
    raw = (getattr(cfg, "gemini_image_size", None) or os.getenv("GEMINI_IMAGE_SIZE") or "").strip()
    if raw.upper() in ("1K", "2K", "4K"):
        return raw.upper()
    return None


def build_arxiv_intel_master_prompt(
    *,
    headline: str,
    topic_title: str,
    slide_role: str,
    semantic_visual_hint: str,
    slide_index: int,
    total_slides: int,
    brand_scene_name: str,
    is_last_slide: bool,
) -> str:
    hl = _normalize_headline(headline)
    topic = _normalize_headline(topic_title or "Tech intelligence", 120)
    hint = (semantic_visual_hint or "").strip()[:400]
    role = (slide_role or "Slide").strip()
    brand = (brand_scene_name or "ArXiv Intel").strip()

    last_extra = ""
    if is_last_slide:
        last_extra = """
Closing slide: add a subtle gold wordmark 'ARXIV INTEL' near the bottom center and one short secondary line in smaller white sans-serif:
'Curated research & tech signals — follow for daily updates.'
Keep the main 3D focal subject centered; do not add a black or grey caption bar."""

    return f"""
A professional, high-fidelity 3D isometric technical illustration for the premium editorial brand "{brand}".

Slide {slide_index} of {total_slides} — narrative role: {role}.
Topic context: {topic}.
Visual direction: {hint if hint else "Abstract metaphor for the headline — sleek chips, glass panels, data pathways, minimal clutter."}

Headline to render EXACTLY (spelling, punctuation): "{hl}"
Typography: place this headline in clean, legible white professional sans-serif letters integrated into the 3D scene at the TOP of the frame (as if part of the environment — e.g. frosted glass sign, extruded type, or luminous panel). No misspellings. No extra words in the headline.

Aesthetic: minimalist 3D isometric render, clean studio lighting, product-catalog / whitepaper diagram quality, hyper-realistic materials, cinematic atmosphere, sharp depth of field, macro detail on edges.
Color palette (mandatory): deep navy environment, electric cyan accents, subtle gold trim, soft amber rim light — "{brand}" technical theme.

Composition: one central hero object or metaphor (abstract tech, circuitry, glass volumes) with glowing cyan edges; transparent and satin-metal materials; faint gold highlights. Shallow depth of field. Generous negative space. No photorealistic human faces. No cluttered collage.

Forbidden: no semi-transparent grey or black lower-third bars, no caption boxes, no subtitles strip behind the headline, no stock-photo news template, no watermark from other brands.
{last_extra}

Format: single editorial frame suitable for Instagram portrait feed (tall).
""".strip()


def _extract_image_from_response(response: object) -> Optional[Image.Image]:
    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content is not None else None
        if not parts:
            continue
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline is not None:
                data = getattr(inline, "data", None)
                if data:
                    try:
                        return Image.open(io.BytesIO(data)).convert("RGB")
                    except OSError:
                        continue
            # Some SDK versions expose as_image()
            if hasattr(part, "as_image"):
                try:
                    im = part.as_image()  # type: ignore[no-untyped-call]
                    if im is not None:
                        return im.convert("RGB")
                except (OSError, ValueError, AttributeError):
                    continue
    return None


def _fit_canvas(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    return ImageOps.fit(img.convert("RGB"), (target_w, target_h), method=Image.Resampling.LANCZOS)


def _generate_slide_pil(
    client: genai.Client,
    model_id: str,
    prompt: str,
    *,
    aspect_ratio: str,
    image_size: str | None,
) -> Image.Image:
    image_cfg_kw: dict = {"aspect_ratio": aspect_ratio}
    if image_size:
        image_cfg_kw["image_size"] = image_size
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(**image_cfg_kw),
    )
    response = client.models.generate_content(
        model=model_id,
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
        config=config,
    )
    img = _extract_image_from_response(response)
    if img is None:
        raise RuntimeError("Gemini returned no image bytes in response")
    return img


def try_render_gemini_carousel(
    cfg: AppConfig,
    slug: str,
    slide_texts: Sequence[str],
    out_dir: Path,
    *,
    topic_title: str = "",
    cover_headline: str = "",
    overlay_texts: Optional[Sequence[str]] = None,
    visual_prompts: Optional[Sequence[str]] = None,
    post_template: str = "carousel_standard",
    profile_path: str = "",
) -> Optional[List[str]]:
    """
    Render carousel JPEGs via Gemini image model + light post-process (no text overlay plates).

    overlay_texts, if provided, overrides slide_texts (matches legacy call sites).
    profile_path is ignored for layout (CTA is generated in-scene on the last slide).
    """
    _ = (post_template, profile_path)
    api_key = (getattr(cfg, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        log_stage(_LOG, "gemini_carousel_skip", "skipped", extra={"slug": slug, "reason": "no_api_key"})
        return None

    texts = list(overlay_texts if overlay_texts is not None else slide_texts)
    if not texts:
        return None

    gen = CarouselImageGenerator()
    brand = gen._brand  # noqa: SLF001 — matches bytecode helper access pattern
    tw = int(brand.get("canvas_width", brand.get("canvas_size", 1080)))
    th = int(brand.get("canvas_height", int(tw * 1.25)))
    max_bytes = int(brand.get("max_jpeg_bytes", 8_388_608))
    scene_brand = str(brand.get("scene_brand_name", brand.get("slide_label", "ArXiv Intel")))
    roles = list(brand.get("slide_role_labels", []))
    accent = gen._hex_to_rgb(str(brand.get("accent", "#38bdf8")))  # noqa: SLF001
    highlight = gen._hex_to_rgb(str(brand.get("highlight_color", "#fbbf24")))  # noqa: SLF001
    primary = gen._hex_to_rgb(str(brand.get("primary_text", "#f1f5f9")))  # noqa: SLF001
    muted = gen._hex_to_rgb(str(brand.get("muted", "#64748b")))  # noqa: SLF001
    title_fonts = list(brand.get("font_title_candidates", []))
    body_fonts = list(brand.get("font_body_candidates", []))

    aspect = _aspect_ratio_for_request(cfg)
    image_size = _image_size_for_request(cfg)
    client = genai.Client(api_key=api_key)
    models = gemini_image_model_candidates(cfg)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total = len(texts)
    paths: List[str] = []
    vp = list(visual_prompts) if visual_prompts else []

    log_stage(
        _LOG,
        "gemini_carousel_start",
        "rendering",
        extra={"slug": slug, "slides": total, "aspect_ratio": aspect, "models": models},
    )

    for i, body in enumerate(texts, start=1):
        role = roles[i - 1] if i - 1 < len(roles) else f"Slide {i}"
        hint = vp[i - 1] if i - 1 < len(vp) else ""
        headline = (cover_headline.strip() if i == 1 and cover_headline else body).strip()
        headline = _normalize_headline(headline, 200)

        prompt = build_arxiv_intel_master_prompt(
            headline=headline,
            topic_title=topic_title or slug.replace("_", " "),
            slide_role=role,
            semantic_visual_hint=hint,
            slide_index=i,
            total_slides=total,
            brand_scene_name=scene_brand,
            is_last_slide=(i == total),
        )

        raw: Optional[Image.Image] = None
        last_err: Optional[BaseException] = None
        for mid in models:
            try:
                raw = _generate_slide_pil(
                    client,
                    mid,
                    prompt,
                    aspect_ratio=aspect,
                    image_size=image_size,
                )
                if raw is not None:
                    break
            except Exception as e:  # noqa: BLE001
                last_err = e
                if is_gemini_model_unavailable_error(e):
                    _LOG.warning("gemini_image_model_fail try_next model=%s err=%s", mid, e)
                    continue
                _LOG.exception("gemini_image_fatal model=%s", mid)
                raise

        if raw is None:
            _LOG.error("gemini_carousel_abort slug=%s slide=%s err=%s", slug, i, last_err)
            return None

        fitted = _fit_canvas(raw, tw, th)
        composed = compose_editorial_slide(
            fitted,
            role=role,
            body=body,
            slide_idx=i,
            total_slides=total,
            brand_label=str(brand.get("slide_label", "ARXIV INTEL")),
            accent_rgb=accent,
            highlight_rgb=highlight,
            muted_rgb=muted,
            primary_rgb=primary,
            font_title_candidates=title_fonts,
            font_body_candidates=body_fonts,
            topic_kicker=topic_title[:80] if topic_title else "",
            cover_headline=cover_headline if i == 1 else "",
            layout_variant="arxiv_intel_scene",
            profile_path="",
        )

        # Match the existing pipeline naming convention (`slide_01.jpg`, ...).
        out_path = out_dir / f"slide_{i:02d}.jpg"
        save_rgb_jpeg_under_limit(composed, out_path, max_bytes=max_bytes)
        paths.append(str(out_path))
        time.sleep(0.4)

    log_stage(_LOG, "gemini_carousel_done", "ok", extra={"slug": slug, "paths": len(paths)})
    return paths
