#!/usr/bin/env python3
"""
Project entrypoint.

This repo is mostly shipped as recovered bytecode (.pyc) to allow execution even
when sources are missing. However, the previous bootstrap logic in this file
was causing recursion when invoked directly (the loaded pyc was effectively
re-executing this same bootstrap).

We now provide a small, source-based CLI for the operations we need during
development (notably `--post-instagram`).
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType


class _PycRecoveryFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"

    def find_spec(self, fullname: str, path=None, target=None):  # type: ignore[override]
        if not (fullname == "src" or fullname.startswith("src.") or fullname == "testscript" or fullname.startswith("testscript.")):
            return None

        parts = fullname.split(".")
        base = self.root.joinpath(*parts)
        pkg_pyc = base / "__pycache__" / f"__init__.{self.tag}.pyc"
        mod_pyc = base.parent / "__pycache__" / f"{parts[-1]}.{self.tag}.pyc"

        if base.is_dir():
            init_py = base / "__init__.py"
            if init_py.is_file():
                return importlib.util.spec_from_file_location(
                    fullname,
                    init_py,
                    submodule_search_locations=[str(base)],
                )

        if len(parts) > 1:
            parent = self.root.joinpath(*parts[:-1])
            mod_name = parts[-1]
            mod_py = parent / f"{mod_name}.py"
            if mod_py.is_file():
                loader = importlib.machinery.SourceFileLoader(fullname, str(mod_py))
                return importlib.util.spec_from_loader(fullname, loader, is_package=False)

        if pkg_pyc.is_file():
            loader = importlib.machinery.SourcelessFileLoader(fullname, str(pkg_pyc))
            return importlib.util.spec_from_loader(fullname, loader, is_package=True)

        if mod_pyc.is_file():
            loader = importlib.machinery.SourcelessFileLoader(fullname, str(mod_pyc))
            return importlib.util.spec_from_loader(fullname, loader, is_package=False)

        if base.is_dir():
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = [str(base)]
            return spec
        return None


def _run_main_pyc() -> int:
    root = Path(__file__).resolve().parent
    sys.meta_path.insert(0, _PycRecoveryFinder(root))
    main_pyc = root / "__pycache__" / f"main.cpython-{sys.version_info.major}{sys.version_info.minor}.pyc"
    if not main_pyc.is_file():
        raise FileNotFoundError(f"Missing bytecode entrypoint: {main_pyc}")

    loader = importlib.machinery.SourcelessFileLoader("__main__", str(main_pyc))
    spec = importlib.util.spec_from_loader("__main__", loader)
    if spec is None:
        raise RuntimeError("Failed to create module spec for main bytecode")
    module = ModuleType("__main__")
    module.__file__ = str(main_pyc)
    module.__package__ = None
    sys.modules["__main__"] = module
    loader.exec_module(module)
    return 0


def _cli(argv: list[str] | None = None) -> int:
    """
    Minimal CLI wrapper to support publishing from the updated image pipeline.
    """
    import argparse
    import json

    root = Path(__file__).resolve().parent
    # Enable recovered-bytecode imports for `src.*` modules whose sources are missing.
    sys.meta_path.insert(0, _PycRecoveryFinder(root))

    from src.media.image_generator import CarouselImageGenerator
    from src.publish.instagram_publisher import InstagramPublisher
    from src.utils.config import get_config

    parser = argparse.ArgumentParser()
    parser.add_argument("--post-instagram", action="store_true", help="Generate and publish a carousel to Instagram")
    parser.add_argument(
        "--use-pyc-bootstrap",
        action="store_true",
        help="Run the legacy bytecode bootstrap (not recommended).",
    )
    args = parser.parse_args(argv)

    if args.use_pyc_bootstrap:
        return _run_main_pyc()

    if not args.post_instagram:
        parser.print_help()
        return 0

    cfg = get_config()

    # Pick latest generated post as a source of (topic, caption, headlines, visual prompts).
    posts_dir = root / "output" / "posts"
    if not posts_dir.is_dir():
        raise FileNotFoundError(f"Missing posts directory: {posts_dir}")
    candidates = sorted([p for p in posts_dir.glob("*.json") if p.is_file()])
    if not candidates:
        raise FileNotFoundError(f"No post JSON files found in {posts_dir}")
    latest = candidates[-1]
    post = json.loads(latest.read_text(encoding="utf-8"))

    slide_texts: list[str] = list(post.get("poster_headlines") or [])
    if not slide_texts:
        # Fallback: use the slide bodies if poster_headlines are missing.
        slide_texts = list(post.get("slides") or [])
    if not slide_texts:
        raise ValueError(f"Post JSON has no headlines/slides: {latest}")

    cover_headline = (slide_texts[0] or "").strip()
    topic_title = str(post.get("topic") or latest.stem)
    visual_prompts = post.get("visual_prompts") or None
    caption = str(post.get("caption") or "")

    out_dir = root / "output" / "images" / f"cli_instagram_test_{latest.stem}"
    gen = CarouselImageGenerator()
    paths = gen.render_topic_slides(
        topic_slug=latest.stem,
        slide_texts=slide_texts,
        out_dir=out_dir,
        topic_title=topic_title,
        cover_headline=cover_headline,
        overlay_texts=slide_texts,
        visual_prompts=visual_prompts,
        post_template=str(post.get("template_style") or "carousel_standard"),
    )

    if not paths:
        raise RuntimeError("Image generation produced no slides; refusing to publish.")

    publisher = InstagramPublisher(cfg)
    ok, msg = publisher.validate_credentials()
    if not ok:
        raise RuntimeError(f"Instagram credentials invalid: {msg}")

    result = publisher.publish_carousel_from_paths([Path(p) for p in paths], caption=caption)
    # Print the main IDs so user can see what got published.
    media_id = result.get("instagram_media_id")
    print(f"Published to Instagram. instagram_media_id={media_id}")
    return 0


if __name__ == "__main__":
    # Default behavior: use the CLI below (source-based).
    # `--use-pyc-bootstrap` keeps the old behavior for debugging bytecode recovery.
    raise SystemExit(_cli())
