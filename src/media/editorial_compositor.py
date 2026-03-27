"""
Editorial carousel layout: premium bottom text dock + keyword highlights over a visual base.
First slide uses a fixed split "intel hero" template: upper visual, lower large-type panel (readable at thumbnail size).

layout_variant "arxiv_intel_scene": pass-through for Gemini frames (headline baked into the render) — only a thin border.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

HIGHLIGHT_WORDS = frozenset(
    {
        "ai",
        "api",
        "ceo",
        "cto",
        "gpu",
        "llm",
        "ml",
        "ar",
        "vr",
        "iot",
        "saas",
        "ipo",
        "vc",
        "fcc",
        "ban",
        "banned",
        "security",
        "cybersecurity",
        "cloud",
        "startup",
        "billion",
        "million",
        "launch",
        "launches",
        "openai",
        "google",
        "apple",
        "microsoft",
        "amazon",
        "aws",
        "meta",
        "tesla",
        "nvidia",
        "data",
        "center",
        "quantum",
        "chip",
        "defense",
        "policy",
        "tariff",
        "strike",
    }
)


def _blend_rgb(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build_abstract_editorial_background(
    size: int | Tuple[int, int],
    rng: random.Random,
    deep: Tuple[int, int, int],
    mid: Tuple[int, int, int],
    accent: Tuple[int, int, int],
) -> Image.Image:
    """Soft gradient + blurred light pools (no photo — still reads as premium vs flat fill)."""
    if isinstance(size, tuple):
        w, h = size
    else:
        w, h = size, size
    top = _blend_rgb(deep, mid, 0.35)
    bot = deep
    grad = Image.new("RGB", (1, h))
    gp = grad.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        gp[0, y] = _blend_rgb(top, bot, t)
    img = grad.resize((w, h), Image.Resampling.LANCZOS)

    for _ in range(3):
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        base = min(w, h)
        cx = rng.randint(int(w * 0.1), int(w * 0.9))
        cy = rng.randint(int(h * 0.05), int(h * 0.55))
        r = rng.randint(base // 4, base // 2)
        glow = (*accent, rng.randint(35, 90))
        ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=glow)
        blur_r = float(rng.randint(55, 95))
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur_r))
        img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

    try:
        noise = Image.effect_noise((max(w // 4, 64), max(h // 4, 64)), rng.randint(8, 22)).convert("L")
        noise = noise.resize((w, h), Image.Resampling.LANCZOS)
        noise_rgb = Image.merge("RGB", (noise, noise, noise))
        img = Image.blend(img, noise_rgb, 0.04)
    except (AttributeError, OSError, ValueError):
        pass
    return img


def _pick_font(candidates: Sequence[str], size: int) -> ImageFont.ImageFont:
    for p in candidates:
        fp = Path(p)
        if fp.is_file():
            try:
                return ImageFont.truetype(str(fp), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _should_highlight(token: str) -> bool:
    t = re.sub(r"^[^\w]+|[^\w]+$", "", token)
    if not t:
        return False
    low = t.lower()
    if low in HIGHLIGHT_WORDS:
        return True
    if len(t) >= 8 and t[0].isupper():
        return True
    if len(low) >= 10:
        return True
    return False


def _split_headline_body(body: str, *, cover: str, is_first_slide: bool) -> Tuple[str, str]:
    b = (body or "").strip() or "—"
    c = (cover or "").strip()
    if is_first_slide and c:
        rest = b
        if rest.lower().startswith(c.lower()[: min(20, len(c))].lower()):
            rest = b[len(c) :].lstrip(" .—-\n")
        return c[:220], (rest[:400] if rest else "")[:400]
    if "." in b[:200]:
        i = b.find(".")
        return b[: i + 1].strip(), b[i + 1 :].strip()
    if len(b) > 100:
        return b[:100].rsplit(" ", 1)[0] + "…", b[100:].strip()
    return b, ""


def _wrap_words_to_width(
    draw: ImageDraw.ImageDraw,
    words: List[str],
    font: ImageFont.ImageFont,
    max_width: int,
) -> List[List[str]]:
    lines: List[List[str]] = []
    cur: List[str] = []
    for w in words:
        trial = (" ".join(cur + [w])).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines[:5]


def _draw_word_line(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    words: Sequence[str],
    font: ImageFont.ImageFont,
    white: Tuple[int, int, int],
    gold: Tuple[int, int, int],
) -> int:
    cx = x
    max_bottom = y
    for w in words:
        fill = gold if _should_highlight(w) else white
        draw.text((cx, y), w + " ", font=font, fill=fill)
        bbox = draw.textbbox((0, 0), w + " ", font=font)
        cx += bbox[2] - bbox[0]
        max_bottom = max(max_bottom, y + (bbox[3] - bbox[1]))
    return max_bottom


def _draw_centered_word_line(
    draw: ImageDraw.ImageDraw,
    y: int,
    words: Sequence[str],
    font: ImageFont.ImageFont,
    canvas_w: int,
    white: Tuple[int, int, int],
    gold: Tuple[int, int, int],
) -> int:
    """Single headline line, centered, with gold/white keyword emphasis."""
    if not words:
        return y
    line = " ".join(words)
    bbox = draw.textbbox((0, 0), line, font=font)
    line_w = bbox[2] - bbox[0]
    x = max(0, (canvas_w - line_w) // 2)
    return _draw_word_line(draw, x, y, words, font, white, gold)


def compose_cinematic_news_slide(
    base_rgb: Image.Image,
    *,
    headline: str,
    font_title_candidates: List[str],
    font_body_candidates: List[str],
    highlight_rgb: Tuple[int, int, int],
    primary_rgb: Tuple[int, int, int],
    accent_rgb: Tuple[int, int, int],
    handle: str = "",
    logo_path: str = "",
    band_start_frac: float = 0.62,
    gradient_bridge_start: float = 0.45,
    sublines: Optional[Sequence[str]] = None,
    show_handle: bool = True,
    logo_in_band: bool = True,
) -> Image.Image:
    """
    Scroll-stopping “tech news” composite: full-bleed cinematic base (no text in source),
    dark gradient bridge + solid lower band, centered ALL-CAPS headline with gold/white emphasis.

    Matches high-performing IG templates: subject in upper ~60%, type in lower ~40%.
    """
    img = base_rgb.convert("RGB")
    w, h = img.size

    # Soften busy detail behind upcoming type (bridge), then solid band for legibility.
    img = _darken_gradient_overlay(img, gradient_bridge_start)

    band_y = int(h * band_start_frac)
    img = _apply_frosted_band(img, band_y)
    
    # Restore the divider branding (horizontal lines + centered logo)
    _draw_divider_with_logo(img, y=band_y + 18, accent_rgb=accent_rgb, logo_path=(logo_path if logo_in_band else ""))

    draw = ImageDraw.Draw(img)
    margin = 48
    max_tw = w - 2 * margin

    y = band_y + 48
    if show_handle and (handle or "").strip():
        hsmall = _pick_font(font_body_candidates, 22)
        hb = (handle or "").strip()
        bbox = draw.textbbox((0, 0), hb, font=hsmall)
        hx = (w - (bbox[2] - bbox[0])) // 2
        draw.text((hx, y), hb, font=hsmall, fill=(180, 190, 210))
        y += (bbox[3] - bbox[1]) + 20

    raw_head = " ".join((headline or "").split()).strip() or "TECH INTELLIGENCE UPDATE"
    head_words = raw_head.upper().split()

    lo, hi = 38, 64
    best_font = _pick_font(font_title_candidates, lo)
    best_lines: List[List[str]] = []
    for sz in range(hi, lo - 1, -2):
        trial_font = _pick_font(font_title_candidates, sz)
        lines = _wrap_words_to_width(draw, head_words, trial_font, max_tw)
        # Fit within band height
        est = 0
        for _ln in lines[:6]:
            bb = draw.textbbox((0, 0), "Hg", font=trial_font)
            est += bb[3] - bb[1] + 10
        if len(lines) <= 5 and est <= (h - y - 40):
            best_font = trial_font
            best_lines = lines[:5]
            break
    if not best_lines:
        best_font = _pick_font(font_title_candidates, lo)
        best_lines = _wrap_words_to_width(draw, head_words, best_font, max_tw)[:5]

    for line_words in best_lines:
        y = _draw_centered_word_line(draw, y, line_words, best_font, w, primary_rgb, highlight_rgb)
        hb = draw.textbbox((0, 0), "Hg", font=best_font)
        y += hb[3] - hb[1] + 10

    if sublines:
        sub_font = _pick_font(font_body_candidates, 30)
        muted_line = (160, 170, 190)
        y += 8
        for raw in list(sublines)[:2]:
            line = " ".join(str(raw or "").split()).strip()
            if not line:
                continue
            for line_words in _wrap_words_to_width(draw, line.upper().split(), sub_font, max_tw)[:2]:
                y = _draw_centered_word_line(draw, y, line_words, sub_font, w, muted_line, highlight_rgb)
                sb = draw.textbbox((0, 0), "Hg", font=sub_font)
                y += sb[3] - sb[1] + 6

    if logo_path and not logo_in_band:
        _paste_asset_contain(img, logo_path, (36, 28, 36 + 200, 28 + 52))

    return img


def compose_cinematic_blueprint_slide(
    base_rgb: Image.Image,
    *,
    headline: str,
    detail_lines: Sequence[str],
    font_title_candidates: List[str],
    font_body_candidates: List[str],
    highlight_rgb: Tuple[int, int, int],
    primary_rgb: Tuple[int, int, int],
    accent_rgb: Tuple[int, int, int],
    logo_path: str = "",
    band_start_frac: float = 0.60,
    gradient_bridge_start: float = 0.42,
    slide_label: str = "",
    logo_in_band: bool = True,
) -> Image.Image:
    """
    Carousel tail: simpler “slate” — one headline block + short supporting lines (one idea per slide).
    No handle; optional corner logo; optional small slide_label above headline.
    """
    img = base_rgb.convert("RGB")
    w, h = img.size
    img = _darken_gradient_overlay(img, gradient_bridge_start)

    band_y = int(h * band_start_frac)
    img = _apply_frosted_band(img, band_y)
    _draw_divider_with_logo(img, y=band_y + 16, accent_rgb=accent_rgb, logo_path=(logo_path if logo_in_band else ""))

    draw = ImageDraw.Draw(img)
    margin = 48
    max_tw = w - 2 * margin
    y = band_y + 46

    slide_label_s = (slide_label or "").strip()
    if slide_label_s and not (logo_in_band and (logo_path or "").strip()):
        lf = _pick_font(font_body_candidates, 22)
        lab = slide_label_s.upper()
        bbox = draw.textbbox((0, 0), lab, font=lf)
        lx = max(margin, (w - (bbox[2] - bbox[0])) // 2)
        draw.text((lx, y), lab, font=lf, fill=(120, 130, 150))
        y += (bbox[3] - bbox[1]) + 14

    raw_head = " ".join((headline or "").split()).strip() or "DETAIL"
    head_words = raw_head.upper().split()

    lo, hi = 32, 52
    best_font = _pick_font(font_title_candidates, lo)
    best_lines: List[List[str]] = []
    for sz in range(hi, lo - 1, -2):
        trial_font = _pick_font(font_title_candidates, sz)
        lines = _wrap_words_to_width(draw, head_words, trial_font, max_tw)
        est = 0
        for _ln in lines[:4]:
            bb = draw.textbbox((0, 0), "Hg", font=trial_font)
            est += bb[3] - bb[1] + 8
        if len(lines) <= 4 and est <= (h - y - 120):
            best_font = trial_font
            best_lines = lines[:4]
            break
    if not best_lines:
        best_font = _pick_font(font_title_candidates, lo)
        best_lines = _wrap_words_to_width(draw, head_words, best_font, max_tw)[:4]

    for line_words in best_lines:
        y = _draw_centered_word_line(draw, y, line_words, best_font, w, primary_rgb, highlight_rgb)
        hb = draw.textbbox((0, 0), "Hg", font=best_font)
        y += hb[3] - hb[1] + 8

    body_font = _pick_font(font_body_candidates, 26)
    muted = (175, 184, 198)
    y += 10
    for raw in list(detail_lines)[:4]:
        text = " ".join(str(raw or "").split()).strip()
        if not text:
            continue
        clean = text
        if clean.startswith("--"):
            clean = clean[2:].lstrip()
        clean = clean.lstrip("-—•● ").strip()
        for line_words in _wrap_words_to_width(draw, clean.split(), body_font, max_tw)[:2]:
            y = _draw_centered_word_line(draw, y, line_words, body_font, w, muted, highlight_rgb)
            sb = draw.textbbox((0, 0), "Hg", font=body_font)
            y += sb[3] - sb[1] + 4
        if y > h - 36:
            break

    if logo_path and not logo_in_band:
        _paste_asset_contain(img, logo_path, (36, 28, 36 + 200, 28 + 52))

    return img


def _arxiv_intel_scene_frame(
    base_rgb: Image.Image,
    *,
    accent_rgb: Tuple[int, int, int],
    border_px: int = 3,
) -> Image.Image:
    """Pass-through Gemini frame: no text plates, only a subtle brand border."""
    img = base_rgb.convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    edge = _blend_rgb(accent_rgb, (251, 191, 36), 0.35)
    for i in range(border_px):
        draw.rectangle([i, i, w - 1 - i, h - 1 - i], outline=edge)
    return img


def _darken_gradient_overlay(base: Image.Image, start_frac: float) -> Image.Image:
    w, h = base.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    y0 = int(h * start_frac)
    # Start gradient slightly higher for better readability breathing room
    y0 = max(0, y0 - int(h * 0.05))
    for y in range(y0, h):
        t = (y - y0) / max(h - y0, 1)
        a = int(220 * min(1.0, t**1.15))
        od.line([(0, y), (w, y)], fill=(8, 10, 14, a))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def _apply_frosted_band(base: Image.Image, band_y: int) -> Image.Image:
    """
    Replace the harsh black dock with a blurred continuation of the image.
    This keeps the photo/scene feeling continuous while still supporting legible type.
    """
    img = base.convert("RGB")
    w, h = img.size
    y0 = max(0, min(h, int(band_y)))
    if y0 >= h:
        return img

    band = img.crop((0, y0, w, h)).filter(ImageFilter.GaussianBlur(radius=18))
    # Increased tint opacity from 130 -> 160 for improved text readability
    tint = Image.new("RGBA", (w, h - y0), (0, 0, 0, 160))
    band_rgba = Image.alpha_composite(band.convert("RGBA"), tint)

    # Fade-in from top edge so it blends into the scene.
    fade = Image.new("L", (1, h - y0), 0)
    fp = fade.load()
    for y in range(h - y0):
        t = y / max((h - y0 - 1), 1)
        fp[0, y] = int(255 * min(1.0, max(0.0, (t**0.85))))
    fade = fade.resize((w, h - y0), Image.Resampling.LANCZOS)

    out = img.convert("RGBA")
    layer = band_rgba.copy()
    layer.putalpha(fade)
    out.paste(layer, (0, y0), layer)
    return out.convert("RGB")


def _draw_divider_with_logo(canvas: Image.Image, *, y: int, accent_rgb: Tuple[int, int, int], logo_path: str = "") -> None:
    """
    Draw a thin divider line across the slide, optionally with a centered logo "breaking" the line.
    This matches the reference style: the logo feels embedded, not pasted above content.
    """
    img = canvas
    w, h = img.size
    yy = max(0, min(h - 1, int(y)))
    margin = 64
    gap = 150  # default logo gap

    if (logo_path or "").strip():
        # Reserve a gap for the logo and paste the mark directly (no black chip box).
        box = (w // 2 - 98, yy - 28, w // 2 + 98, yy + 40)
        # Keep a small gap so the divider feels embedded under the logo.
        gap = (box[2] - box[0]) + 12

    draw = ImageDraw.Draw(img)
    mid_x = w // 2
    left_end = max(margin, mid_x - gap // 2)
    right_start = min(w - margin, mid_x + gap // 2)
    line_col = _blend_rgb(accent_rgb, (251, 191, 36), 0.22)
    draw.line([(margin, yy), (left_end, yy)], fill=line_col, width=2)
    draw.line([(right_start, yy), (w - margin, yy)], fill=line_col, width=2)

    # Paste logo after drawing the divider so the logo covers the line where it exists.
    if (logo_path or "").strip():
        _paste_asset_contain(img, logo_path, box)


def _auto_transparent_asset(img: Image.Image, tol: int = 24) -> Image.Image:
    rgba = img.convert("RGBA")
    a = rgba.getchannel("A")
    if a.getextrema() != (255, 255):
        return rgba
    rgb = rgba.convert("RGB")
    w, h = rgb.size
    corners = [
        rgb.getpixel((0, 0)),
        rgb.getpixel((w - 1, 0)),
        rgb.getpixel((0, h - 1)),
        rgb.getpixel((w - 1, h - 1)),
    ]
    bg = tuple(int(sum(c[i] for c in corners) / 4) for i in range(3))
    px = rgba.load()
    for yy in range(h):
        for xx in range(w):
            r, g, b, _ = px[xx, yy]
            if abs(r - bg[0]) <= tol and abs(g - bg[1]) <= tol and abs(b - bg[2]) <= tol:
                px[xx, yy] = (r, g, b, 0)
    return rgba


def _extract_profile_tree_mark(img: Image.Image) -> Image.Image:
    """
    Heuristic crop to the *tree mark only* from the provided profile logo renders.
    We intentionally avoid the surrounding "ArXiv Intel" ring text by cropping to the
    inner emblem area and applying a circular alpha mask.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    side = min(w, h)
    # Crop to a centered square, then to an inner square to remove ring text.
    cx, cy = w // 2, h // 2
    half0 = side // 2
    sq = rgba.crop((cx - half0, cy - half0, cx + half0, cy + half0))
    iw, ih = sq.size
    inner = int(min(iw, ih) * 0.64)
    half1 = inner // 2
    inner_sq = sq.crop((iw // 2 - half1, ih // 2 - half1, iw // 2 + half1, ih // 2 + half1))

    # Circular mask so it reads as a clean "mark" on a divider.
    mw, mh = inner_sq.size
    mask = Image.new("L", (mw, mh), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([2, 2, mw - 3, mh - 3], fill=255)
    inner_sq.putalpha(mask)
    return inner_sq


def _paste_asset_contain(canvas: Image.Image, asset_path: Optional[str], box: Tuple[int, int, int, int]) -> None:
    if not asset_path:
        return
    p = Path(asset_path)
    if not p.is_file():
        return
    try:
        logo = _auto_transparent_asset(Image.open(p))
    except OSError:
        return

    # If the asset is one of the generated profile images, crop to the inner tree mark
    # unless it is already a transparent cutout we can use as-is.
    bn = p.name.lower()
    already_cutout = ("trans" in bn) and (logo.getchannel("A").getextrema()[0] < 250)
    if (bn.startswith("ai_profile") and not already_cutout) or (os.getenv("PROFILE_LOGO_MODE") or "").strip().lower() in ("tree", "mark"):
        try:
            logo = _extract_profile_tree_mark(logo)
        except Exception:
            # Best-effort; if cropping fails, fall back to raw.
            pass
    x1, y1, x2, y2 = box
    bw, bh = max(1, x2 - x1), max(1, y2 - y1)
    lw, lh = logo.size
    scale = min(bw / lw, bh / lh)
    nw, nh = max(1, int(lw * scale)), max(1, int(lh * scale))
    logo = logo.resize((nw, nh), Image.Resampling.LANCZOS)
    ox = x1 + (bw - nw) // 2
    oy = y1 + (bh - nh) // 2
    canvas.paste(logo, (ox, oy), logo)


def _compose_cover_intel_hero(
    base_rgb: Image.Image,
    *,
    body: str,
    cover_headline: str,
    brand_label: str,
    accent_rgb: Tuple[int, int, int],
    highlight_rgb: Tuple[int, int, int],
    primary_rgb: Tuple[int, int, int],
    font_title_candidates: List[str],
    font_body_candidates: List[str],
) -> Image.Image:
    """
    Split template: top ~46% = clean visual (minimal overlay), bottom ~54% = solid panel + LARGE type.
    Designed for feed thumbnails: headline must dominate, not tiny body copy.
    """
    img = base_rgb.convert("RGB")
    w, h = img.size
    split_y = int(h * 0.46)

    top = img.crop((0, 0, w, split_y))
    # Light vignette on lower edge of visual only (bridge into panel)
    bridge = Image.new("RGBA", (w, split_y), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bridge)
    for y in range(max(0, split_y - 48), split_y):
        t = (y - (split_y - 48)) / 48.0
        a = int(70 * t)
        bd.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    top = Image.alpha_composite(top.convert("RGBA"), bridge).convert("RGB")

    out = Image.new("RGB", (w, h), (3, 4, 8))
    out.paste(top, (0, 0))

    panel_top = split_y
    draw = ImageDraw.Draw(out)
    draw.rectangle([0, panel_top, w, h], fill=(5, 6, 10))
    bar_h = 8
    draw.rectangle([0, panel_top, w, panel_top + bar_h], fill=accent_rgb)

    margin = 52
    max_tw = w - 2 * margin
    y = panel_top + bar_h + 28

    chip = (brand_label or "AI TECH INTEL").upper().strip()
    chip_font = _pick_font(font_body_candidates, 28)
    draw.text((margin, y), chip, font=chip_font, fill=highlight_rgb)
    y += 40

    head, sub = _split_headline_body(body, cover=cover_headline, is_first_slide=True)
    head_words = head.split()

    lo, hi = 44, 86
    best_font = _pick_font(font_title_candidates, lo)
    best_lines: List[List[str]] = []
    for sz in range(hi, lo - 1, -2):
        trial_font = _pick_font(font_title_candidates, sz)
        lines = _wrap_words_to_width(draw, head_words, trial_font, max_tw)
        est_h = 0
        for _ln in lines[:4]:
            bb = draw.textbbox((0, 0), "Hg", font=trial_font)
            est_h += bb[3] - bb[1] + 8
        if len(lines) <= 4 and est_h <= (h - y - 120):
            best_font = trial_font
            best_lines = lines[:4]
            break
    if not best_lines:
        best_font = _pick_font(font_title_candidates, lo)
        best_lines = _wrap_words_to_width(draw, head_words, best_font, max_tw)[:4]

    for line_words in best_lines:
        y = _draw_word_line(draw, margin, y, line_words, best_font, primary_rgb, highlight_rgb)
        hb = draw.textbbox((0, 0), "Hg", font=best_font)
        y += hb[3] - hb[1] + 10

    if sub and y < h - 72:
        y += 12
        sub_font = _pick_font(font_body_candidates, 32)
        for line_words in _wrap_words_to_width(draw, sub.split(), sub_font, max_tw)[:2]:
            y = _draw_word_line(draw, margin, y, line_words, sub_font, primary_rgb, highlight_rgb)
            sb = draw.textbbox((0, 0), "Hg", font=sub_font)
            y += sb[3] - sb[1] + 6

    return out


def compose_editorial_slide(
    base_rgb: Image.Image,
    *,
    role: str,
    body: str,
    slide_idx: int,
    total_slides: int,
    brand_label: str,
    accent_rgb: Tuple[int, int, int],
    highlight_rgb: Tuple[int, int, int],
    muted_rgb: Tuple[int, int, int],
    primary_rgb: Tuple[int, int, int],
    font_title_candidates: List[str],
    font_body_candidates: List[str],
    topic_kicker: str = "",
    cover_headline: str = "",
    gradient_start_frac: float = 0.34,
    swipe_hint: str = "SWIPE FOR MORE →",
    layout_variant: str = "left_dock",
    logo_path: str = "",
    profile_path: str = "",
) -> Image.Image:
    _ = (muted_rgb, topic_kicker, role, swipe_hint, logo_path)
    w, h = base_rgb.size

    if layout_variant == "arxiv_intel_scene":
        return _arxiv_intel_scene_frame(base_rgb, accent_rgb=accent_rgb)

    if slide_idx == total_slides and total_slides >= 5 and profile_path:
        img = base_rgb.convert("RGB")
        img = _darken_gradient_overlay(img, gradient_start_frac)
        draw = ImageDraw.Draw(img)
        margin = 56
        panel_top = int(h * 0.50)
        panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        if hasattr(pd, "rounded_rectangle"):
            pd.rounded_rectangle([margin - 8, panel_top, w - margin + 8, h - 56], radius=28, fill=(6, 10, 16, 170))
        else:
            pd.rectangle([margin - 8, panel_top, w - margin + 8, h - 56], fill=(6, 10, 16, 170))
        img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
        draw = ImageDraw.Draw(img)
        avatar_box = (margin + 8, panel_top + 18, margin + 212, panel_top + 222)
        _paste_asset_contain(img, profile_path, avatar_box)
        title_font = _pick_font(font_title_candidates, 40)
        body_font = _pick_font(font_body_candidates, 26)
        stat_font = _pick_font(font_body_candidates, 24)
        tx = margin + 238
        y = panel_top + 26
        draw.text((tx, y), "Follow for verified tech intelligence", font=title_font, fill=primary_rgb)
        y += 60
        blurb = (
            "We scan 50+ daily tech stories, verify signals across trusted sources, "
            "and publish concise explainers you can act on."
        )
        for line_words in _wrap_words_to_width(draw, blurb.split(), body_font, w - tx - margin)[:4]:
            y = _draw_word_line(draw, tx, y, line_words, body_font, primary_rgb, highlight_rgb)
            sb = draw.textbbox((0, 0), "Hg", font=body_font)
            y += sb[3] - sb[1] + 3
        y += 6
        for stat in [
            "50+ stories monitored daily",
            "Multi-source verification pipeline",
            "Actionable AI and startup insights",
        ]:
            draw.text((tx, y), f"- {stat}", font=stat_font, fill=highlight_rgb)
            y += 32
        return img

    if layout_variant in ("cover_impact", "hero_intel_cover"):
        return _compose_cover_intel_hero(
            base_rgb,
            body=body,
            cover_headline=cover_headline,
            brand_label=brand_label,
            accent_rgb=accent_rgb,
            highlight_rgb=highlight_rgb,
            primary_rgb=primary_rgb,
            font_title_candidates=font_title_candidates,
            font_body_candidates=font_body_candidates,
        )

    img = base_rgb.convert("RGB")
    img = _darken_gradient_overlay(img, gradient_start_frac)
    draw = ImageDraw.Draw(img)

    margin = 56
    headline_font = _pick_font(font_title_candidates, 46 if slide_idx == 1 else 40)
    sub_font = _pick_font(font_body_candidates, 28)

    if layout_variant == "center_dock":
        text_top = int(h * 0.54)
        margin = 84
    elif layout_variant == "split_dock":
        text_top = int(h * 0.49)
        margin = 64
    elif layout_variant == "narrative_minimal":
        text_top = int(h * 0.12)
        margin = 88
    else:
        text_top = int(h * 0.51)

    if layout_variant != "narrative_minimal":
        jitter = ((slide_idx * 17) % 15) - 7
        text_top = max(int(h * 0.44), min(int(h * 0.62), text_top + jitter))

    y = text_top

    head, sub = _split_headline_body(body, cover=cover_headline, is_first_slide=(slide_idx == 1))
    head_words = head.split()
    max_tw = w - 2 * margin

    plate_top = max(int(h * (0.06 if layout_variant == "narrative_minimal" else 0.52)), y - 14)
    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    plate_bottom = h - 44 if layout_variant != "narrative_minimal" else int(h * 0.74)
    plate_alpha = 150 if layout_variant == "narrative_minimal" else 72
    if hasattr(pd, "rounded_rectangle"):
        pd.rounded_rectangle(
            [margin - 16, plate_top, w - margin + 16, plate_bottom],
            radius=24,
            fill=(5, 8, 12, plate_alpha),
        )
    else:
        pd.rectangle([margin - 16, plate_top, w - margin + 16, plate_bottom], fill=(5, 8, 12, plate_alpha))
    img = Image.alpha_composite(img.convert("RGBA"), plate).convert("RGB")
    draw = ImageDraw.Draw(img)
    for line_words in _wrap_words_to_width(draw, head_words, headline_font, max_tw):
        y = _draw_word_line(draw, margin, y, line_words, headline_font, primary_rgb, highlight_rgb)
        hb = draw.textbbox((0, 0), "Hg", font=headline_font)
        y += hb[3] - hb[1] + 6

    if sub:
        y += 8
        for line_words in _wrap_words_to_width(draw, sub.split(), sub_font, max_tw)[:4]:
            y = _draw_word_line(draw, margin, y, line_words, sub_font, primary_rgb, highlight_rgb)
            sb = draw.textbbox((0, 0), "Hg", font=sub_font)
            y += sb[3] - sb[1] + 4

    return img
