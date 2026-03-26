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
        "--post-json",
        default=None,
        metavar="POST_JSON",
        help="Use a specific post JSON file (path or filename under output/posts/) instead of the newest one.",
    )
    parser.add_argument(
        "--render-post",
        nargs="?",
        const="",
        default=None,
        metavar="POST_JSON",
        help="Render carousel JPEGs from a post JSON (default: newest file in output/posts/). Does not publish.",
    )
    parser.add_argument(
        "--use-pyc-bootstrap",
        action="store_true",
        help="Run the legacy bytecode bootstrap (not recommended).",
    )
    args = parser.parse_args(argv)

    if args.use_pyc_bootstrap:
        return _run_main_pyc()

    if not args.post_instagram and args.render_post is None:
        parser.print_help()
        return 0

    if args.post_instagram and args.render_post is not None:
        parser.error("Choose either --post-instagram or --render-post, not both.")

    cfg = get_config()
    posts_dir = root / "output" / "posts"
    if not posts_dir.is_dir():
        raise FileNotFoundError(f"Missing posts directory: {posts_dir}")
    post_candidates = sorted([p for p in posts_dir.glob("*.json") if p.is_file()])
    if not post_candidates:
        raise FileNotFoundError(f"No post JSON files found in {posts_dir}")

    def _resolve_post_path(spec: str | None) -> Path:
        if spec is None or str(spec).strip() == "":
            return post_candidates[-1]
        p = Path(spec)
        if p.is_file():
            return p.resolve()
        alt = (posts_dir / spec).resolve()
        if alt.is_file():
            return alt
        raise FileNotFoundError(f"Post JSON not found: {spec}")

    post_spec: str | None = args.post_json
    if args.post_instagram:
        # For publishing, --post-json selects the target; otherwise we default to newest.
        post_spec = post_spec if post_spec and str(post_spec).strip() else None
    else:
        # For rendering, --render-post selects the target when provided.
        if not (post_spec and str(post_spec).strip()):
            post_spec = args.render_post

    post_path = _resolve_post_path(post_spec)
    post = json.loads(post_path.read_text(encoding="utf-8"))

    slide_texts: list[str] = list(post.get("poster_headlines") or [])
    if not slide_texts:
        slide_texts = list(post.get("slides") or [])
    if not slide_texts:
        raise ValueError(f"Post JSON has no headlines/slides: {post_path}")

    cover_headline = str(post.get("cover_headline") or (slide_texts[0] or "")).strip()
    topic_title = str(post.get("topic") or post_path.stem)
    visual_prompts = post.get("visual_prompts") or None
    caption = str(post.get("caption") or "")
    slide_bodies = list(post.get("slides") or [])

    out_slug = post_path.stem
    out_dir = root / "output" / "images" / (f"render_{out_slug}" if args.render_post is not None else f"cli_instagram_test_{out_slug}")
    gen = CarouselImageGenerator()
    paths = gen.render_topic_slides(
        topic_slug=out_slug,
        slide_texts=slide_texts,
        out_dir=out_dir,
        topic_title=topic_title,
        cover_headline=cover_headline,
        overlay_texts=slide_texts,
        visual_prompts=visual_prompts,
        post_template=str(post.get("template_style") or "carousel_standard"),
        slide_bodies=slide_bodies if slide_bodies else None,
        story_post=post,
    )

    if not paths:
        raise RuntimeError("Image generation produced no slides.")

    if args.render_post is not None:
        print(f"Rendered {len(paths)} slides to {out_dir}")
        for p in paths:
            print(Path(p).resolve())
        return 0

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
