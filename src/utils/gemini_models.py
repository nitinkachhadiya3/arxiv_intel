"""Gemini model ids + fallbacks for text and image generation."""

from __future__ import annotations

import os
from typing import List


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def gemini_fallback_model() -> str:
    return _env("GEMINI_MODEL_FALLBACK", "gemini-2.5-pro")


def gemini_model_candidates(primary: str | None = None) -> List[str]:
    """Ordered list: configured model first, then fallback (deduped)."""
    p = (primary or _env("GEMINI_MODEL", "")).strip()
    fb = gemini_fallback_model()
    out: List[str] = []
    seen: set[str] = set()
    for m in (p, fb):
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _image_primary_from_cfg(cfg_or_str: object | None) -> str:
    if cfg_or_str is None:
        return _env("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    if isinstance(cfg_or_str, str):
        s = cfg_or_str.strip()
        return s or _env("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    for attr in ("gemini_image_model", "gemini_image_model_id"):
        v = getattr(cfg_or_str, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return _env("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")


def _image_fallback_from_cfg(cfg_or_str: object | None) -> str:
    if cfg_or_str is not None and not isinstance(cfg_or_str, str):
        v = getattr(cfg_or_str, "gemini_image_model_fallback", None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return _env("GEMINI_IMAGE_MODEL_FALLBACK", "")


def gemini_image_model_candidates(cfg_or_str: object | None = None) -> List[str]:
    """Primary from config or GEMINI_IMAGE_MODEL, plus optional fallback env / field."""
    primary = _image_primary_from_cfg(cfg_or_str)
    fb = _image_fallback_from_cfg(cfg_or_str)
    out: List[str] = []
    seen: set[str] = set()
    for m in (primary, fb):
        if m and m not in seen:
            seen.add(m)
            out.append(m)
    return out


def is_gemini_model_unavailable_error(exc: BaseException) -> bool:
    """True when retrying with another model id is reasonable."""
    msg = str(exc).lower()
    needles = (
        "not found",
        "no longer available",
        "not available",
        "invalid",
        "does not exist",
        "404",
        "unsupported",
    )
    return any(n in msg for n in needles)
