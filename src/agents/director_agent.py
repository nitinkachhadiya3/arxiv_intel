"""
DirectorAgent — the orchestrator of the sports multi-agent system.

Flow:
  1. DataAgent fetches live match context
  2. VisualAgent builds the slide plan (visual vs text, worlds, prompts)
  3. DirectorAgent calls Gemini to write slide captions based on real data
  4. Merges captions + image prompts into final slide objects
  5. Returns ready-to-render carousel data

All agents communicate through a shared `context` dict.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from src.agents.data_agent import DataAgent
from src.agents.visual_agent import VisualAgent

logger = logging.getLogger(__name__)


class DirectorAgent:
    """
    The Creative Director: orchestrates DataAgent and VisualAgent,
    then uses the LLM to write compelling captions for each slide.
    """

    def __init__(self):
        self.data_agent = DataAgent()
        self.visual_agent = VisualAgent()

    def generate_sports_post(
        self,
        query: str = "IPL 2026 latest match",
        slide_count: int = 5,
        draft_count: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Full pipeline: fetch data → plan visuals → write captions.
        Returns a list of draft dicts: [{'slides': [...], 'match_data': {...}}]
        """

        # ── Step 1: DataAgent fetches live match intelligence ──────────────
        logger.info("DirectorAgent: calling DataAgent…")
        context: Dict[str, Any] = {}
        match_data = self.data_agent.fetch_live_match(query)
        context["match_data"] = match_data
        hashtag_block = self.data_agent.build_hashtag_block(match_data)
        context["hashtag_block"] = hashtag_block
        logger.info("DirectorAgent: match='%s', hashtags=%d", match_data.get("match_title"), len(hashtag_block))

        # ── Step 2: VisualAgent plans slides ──────────────────────────────
        logger.info("DirectorAgent: calling VisualAgent…")
        slide_plan = self.visual_agent.decide_slide_plan(match_data, slide_count)
        context["slide_plan"] = slide_plan
        logger.info("DirectorAgent: slide plan built – %d slides, %d visual",
                    len(slide_plan), sum(1 for s in slide_plan if s["visual_flag"]))

        # ── Step 3: LLM writes captions for each slide ────────────────────
        logger.info("DirectorAgent: calling LLM for captions…")
        drafts = []
        for _ in range(draft_count):
            slides = self._write_captions(match_data, slide_plan, hashtag_block)
            drafts.append({"slides": slides, "match_data": match_data})

        return drafts

    def _write_captions(
        self,
        match_data: Dict[str, Any],
        slide_plan: List[Dict[str, Any]],
        hashtag_block: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini to write punchy, data-driven captions.
        Falls back to template captions if the API call fails.
        """
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return self._template_captions(match_data, slide_plan, hashtag_block)

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)

            system_prompt = self._build_caption_prompt(match_data, slide_plan, hashtag_block)

            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=system_prompt)])],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                ),
            )
            text = getattr(resp, "text", "") or ""
            m = re.search(r"\[[\s\S]*\]", text)
            if m:
                raw_slides = json.loads(m.group(0))
                # Merge captions with slide plan
                merged = []
                for i, plan_slide in enumerate(slide_plan):
                    raw = raw_slides[i] if i < len(raw_slides) else {}
                    merged.append({
                        "slide_index": plan_slide["slide_index"],
                        "caption": raw.get("caption", f"Slide {i+1}"),
                        "image_prompt": plan_slide["image_prompt"],
                        "visual_flag": plan_slide["visual_flag"],
                        "world_id": plan_slide["world_id"],
                        "scene_hint": plan_slide["scene_hint"],
                    })
                return merged
        except Exception as exc:
            logger.warning("DirectorAgent: LLM caption failed – %s", exc)

        return self._template_captions(match_data, slide_plan, hashtag_block)

    def _build_caption_prompt(
        self,
        match_data: Dict[str, Any],
        slide_plan: List[Dict[str, Any]],
        hashtag_block: List[str],
    ) -> str:
        """Build the LLM prompt for writing slide captions."""
        performers_text = "\n".join(
            f"  - {p['name']} ({p['team']}): {p['stat']} [{p['role']}]"
            for p in match_data.get("key_performers", [])
        )
        moments_text = "\n".join(f"  - {m}" for m in match_data.get("trending_moments", []))
        records_text = "\n".join(f"  - {r}" for r in match_data.get("records_broken", []))
        hashtag_str = " ".join(hashtag_block[:20])

        slide_roles = []
        for s in slide_plan:
            role = "VISUAL" if s["visual_flag"] else "TEXT-ONLY DATA"
            slide_roles.append(f"Slide {s['slide_index']} [{role}]: Scene = {s['scene_hint']}")
        slides_text = "\n".join(slide_roles)

        return f"""You are an expert IPL sports Instagram content creator. Write electrifying captions for a 5-slide Instagram carousel post.

MATCH DATA:
- Match: {match_data.get('match_title', 'IPL 2026')}
- Score: {match_data.get('current_score', {}).get('team', 'N/A')}
- Phase: {match_data.get('match_phase', 'N/A')}
- Venue: {match_data.get('venue', 'N/A')}
- Crowd Mood: {match_data.get('crowd_mood', 'Electric')}
- Insight: {match_data.get('insight_text', '')}

KEY PERFORMERS:
{performers_text}

RECORDS BROKEN:
{records_text}

TRENDING MOMENTS:
{moments_text}

SLIDE PLAN (5 slides):
{slides_text}

INSTRUCTIONS:
- Write a punchy caption for EACH slide (1-3 lines, max 150 chars per slide).
- Use emojis strategically for emotion (🏏 🔥 💥 🎯 ⚡ 🏆 👑).
- Slide 1 MUST be a dramatic hook that makes someone stop scrolling.
- Slides 2-3 are DATA slides — write crisp factual captions referencing real stats above.
- Slide 4 is a KEY PERFORMER highlight — make it personal and powerful.
- Slide 5 is the CTA/crowd energy slide — end with a question or bold statement.
- For the LAST slide ONLY: add these hashtags at the end: {hashtag_str}

Return ONLY a JSON array of 5 objects with key "caption":
[{{"caption": "..."}} , {{"caption": "..."}} , ...]"""

    def _template_captions(
        self,
        match_data: Dict[str, Any],
        slide_plan: List[Dict[str, Any]],
        hashtag_block: List[str],
    ) -> List[Dict[str, Any]]:
        """Fallback captions when LLM is unavailable."""
        title = match_data.get("match_title", "IPL 2026")
        score = match_data.get("current_score", {}).get("team", "Score updating…")
        hero = match_data.get("hero_player", {}).get("name", "the star")
        performers = match_data.get("key_performers", [])
        records = match_data.get("records_broken", [])
        insight = match_data.get("insight_text", "Cricket at its finest.")
        hashtag_str = " ".join(hashtag_block[:20])

        templates = [
            f"🔥 {title}\nThis one's for the history books. 👑",
            f"📊 Live Score: {score}\n{insight}",
            f"💥 {records[0] if records else 'Records are being shattered tonight.'}\n#Historic",
            f"🎯 {performers[0]['name'] if performers else hero} — absolutely ON FIRE tonight! 🏏",
            f"⚡ What a match! Drop a 🏏 if you're watching live!\n\n{hashtag_str}",
        ]

        slides = []
        for i, plan_slide in enumerate(slide_plan):
            caption = templates[i] if i < len(templates) else f"Slide {i+1} — {title}"
            slides.append({
                "slide_index": plan_slide["slide_index"],
                "caption": caption,
                "image_prompt": plan_slide["image_prompt"],
                "visual_flag": plan_slide["visual_flag"],
                "world_id": plan_slide["world_id"],
                "scene_hint": plan_slide["scene_hint"],
            })
        return slides
