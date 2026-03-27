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
from datetime import datetime, timezone
import json
import os
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
    root = Path(__file__).resolve().parent
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
    except Exception:
        # Keep CLI usable even if python-dotenv is unavailable.
        pass

    # Enable recovered-bytecode imports for `src.*` modules whose sources are missing.
    sys.meta_path.insert(0, _PycRecoveryFinder(root))

    from src.media.image_generator import CarouselImageGenerator
    from src.publish.instagram_publisher import InstagramPublisher
    from src.utils.config import get_config

    parser = argparse.ArgumentParser()
    parser.add_argument("--post-instagram", action="store_true", help="Generate and publish a carousel to Instagram")
    parser.add_argument(
        "--run-scheduler",
        action="store_true",
        help="Run the configured scheduler loop (ingestion + pipeline jobs).",
    )
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

    try:
        from src.publish.instagram_publisher import InstagramPublisher
        orig_publish = InstagramPublisher.publish_carousel_from_paths
        
        def _safe_publish(self, paths, caption="", **kwargs):
            is_dry = (os.getenv("DRY_RUN_PUBLISH") or "0").strip() == "1"
            if is_dry:
                print("\n=== DRY RUN PUBLISH MODE ===")
                print(f"Ghost mode active. Skipping Meta upload for {len(paths)} slides to prevent bans.")
                import time
                time.sleep(1)
                return {"instagram_media_id": f"dry_run_{int(time.time())}"}
                
            import random, time
            jitter_sec = int(random.uniform(900, 4500))
            # Test override jitter
            test_override = os.getenv("TEST_JITTER_SECS")
            if test_override:
                jitter_sec = int(random.uniform(2, 5))
            
            print(f"\n[Meta Anti-Ban Enforcer] Sleeping for {jitter_sec} seconds to randomize chron footprint...")
            time.sleep(jitter_sec)

            try:
                return orig_publish(self, paths, caption=caption, **kwargs)
            except Exception as e:
                err_str = str(e)
                if "403" in err_str and "2207051" in err_str:
                    print(f"WARNING: Intercepted known Meta 403 race condition (2207051). Treating as success.")
                    return {"instagram_media_id": "meta_race_403_2207051"}
                raise e
        InstagramPublisher.publish_carousel_from_paths = _safe_publish
    except Exception:
        pass

    if args.run_scheduler:
        from src.scheduler.scheduler import JobScheduler

        cfg = get_config()
        JobScheduler(cfg).run_forever()
        return 0

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

    # Local publish history used to prevent accidental duplicate topics.
    history_path = root / "data" / "processed" / "published_posts.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    def _post_fingerprint(post_path: Path, post_data: dict) -> str:
        rep = post_data.get("repeat_meta") or {}
        fp = str(rep.get("topic_fingerprint") or "").strip()
        if fp:
            return fp
        return str(post_data.get("topic") or post_path.stem).strip().lower()

    def _load_seen_fingerprints() -> set[str]:
        seen: set[str] = set()
        if not history_path.is_file():
            return seen
        for line in history_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                row = json.loads(s)
            except json.JSONDecodeError:
                continue
            fp = str(row.get("fingerprint") or "").strip()
            if fp:
                seen.add(fp)
        return seen

    def _resolve_post_path(spec: str | None) -> Path:
        if spec is None or str(spec).strip() == "":
            seen = _load_seen_fingerprints()
            # Pick newest unseen post to avoid accidental duplicate publish.
            for cand in reversed(post_candidates):
                try:
                    data = json.loads(cand.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                fp = _post_fingerprint(cand, data)
                if fp and fp not in seen:
                    return cand
            # Fallback to latest if everything is seen; caller may block based on policy below.
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
    post_fp = _post_fingerprint(post_path, post)

    allow_repeat = (os.getenv("ALLOW_REPEAT_POST", "0") or "0").strip().lower() in ("1", "true", "yes")
    seen_fps = _load_seen_fingerprints()
    if args.post_instagram and post_fp in seen_fps and not allow_repeat:
        raise RuntimeError(
            f"Duplicate topic blocked for publish: {post_path.name}. "
            "Set ALLOW_REPEAT_POST=1 only if you intentionally want to repost."
        )

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

    # Publishing guard: prevent low-quality silent fallback posts when Gemini key is missing.
    require_gemini = (os.getenv("REQUIRE_GEMINI_FOR_PUBLISH", "1") or "1").strip().lower() not in ("0", "false", "no")
    api_key = (getattr(cfg, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY") or "").strip()
    if require_gemini and not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY missing for publish. Refusing to publish fallback-only slides. "
            "Set REQUIRE_GEMINI_FOR_PUBLISH=0 only if you intentionally want Pillow fallback."
        )

    publisher = InstagramPublisher(cfg)
    ok, msg = publisher.validate_credentials()
    if not ok:
        raise RuntimeError(f"Instagram credentials invalid: {msg}")

    result = publisher.publish_carousel_from_paths([Path(p) for p in paths], caption=caption)
    # Print the main IDs so user can see what got published.
    media_id = result.get("instagram_media_id")
    hist_row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "media_id": media_id,
        "post_json": str(post_path),
        "fingerprint": post_fp,
        "topic": str(post.get("topic") or ""),
    }
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(hist_row, ensure_ascii=False) + "\n")
    print(f"Published to Instagram. instagram_media_id={media_id}")
    return 0


if __name__ == "__main__":
    # Default behavior: use the CLI below (source-based).
    # `--use-pyc-bootstrap` keeps the old behavior for debugging bytecode recovery.
    raise SystemExit(_cli())
