"""
Sports pipeline integration for src/bot/core.py.

Adds generate_sports_previews() — a parallel to generate_custom_previews()
that routes through the DirectorAgent multi-agent system.
"""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List

from src.bot.cloudinary_uploader import CloudinaryUploader
from src.bot.state import state
from src.agents.director_agent import DirectorAgent


def generate_sports_previews(query: str = "IPL 2026 today match") -> List[Dict[str, Any]]:
    """
    Full sports carousel generation via multi-agent system.

    Returns a list of preview dicts compatible with the existing bot handler:
      [{ 'uuid', 'caption', 'media_urls', 'match_data' }]
    """
    # Lazy env-load
    if not os.getenv("GEMINI_API_KEY"):
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env", override=True)
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if key:
            os.environ["GOOGLE_API_KEY"] = key

    director = DirectorAgent()
    drafts = director.generate_sports_post(query=query, slide_count=5, draft_count=1)

    previews = []
    for draft in drafts:
        slides = draft.get("slides", [])
        match_data = draft.get("match_data", {})

        if not slides:
            continue

        # Build visual_prompts and visual_flags for the renderer
        visual_prompts = [s.get("image_prompt", "") for s in slides]
        visual_flags = [s.get("visual_flag", True) for s in slides]
        slide_texts = [s.get("caption", "") for s in slides]
        match_title = match_data.get("match_title", "IPL 2026")

        # Use existing carousel renderer
        from src.media.image_generator import CarouselImageGenerator
        generator = CarouselImageGenerator()
        slug = f"sports_{uuid.uuid4().hex[:8]}"

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            media_paths = generator.render_topic_slides(
                topic_slug=slug,
                slide_texts=slide_texts,
                out_dir=out_dir,
                topic_title=match_title,
                cover_headline=slide_texts[0][:80] if slide_texts else match_title,
                visual_prompts=visual_prompts,
                story_post={**match_data, "visual_flags": visual_flags},
            )
            media_urls = [CloudinaryUploader.upload_file(str(p)) for p in media_paths]

        preview_uuid = str(uuid.uuid4())
        # Final caption = last slide caption (which includes hashtags)
        final_caption = slide_texts[-1] if slide_texts else match_title
        preview = {
            "uuid": preview_uuid,
            "caption": final_caption,
            "media_urls": media_urls,
            "match_data": match_data,
        }
        previews.append(preview)
        state.update_child("sports", preview_uuid, preview)

    return previews
