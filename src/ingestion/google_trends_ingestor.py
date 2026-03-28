"""
Google Trends Ingestor — fetches trending searches, filters for AI/tech,
enriches with Gemini for Instagram-ready content.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import yaml
from pathlib import Path


_TECH_SEEDS = {
    "ai", "artificial intelligence", "machine learning", "llm", "gpt",
    "openai", "google", "microsoft", "nvidia", "apple", "meta", "amazon",
    "robot", "autonomous", "agent", "chip", "cloud", "startup", "quantum",
    "agentic", "automation", "security", "regulation", "enterprise",
}


def _load_trends_config() -> Dict:
    """Load trends config from settings.yaml."""
    settings_path = Path("config/settings.yaml")
    if settings_path.exists():
        with open(settings_path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("trends", {})
    return {"geo": "IN"}


def fetch_trending_searches(geo: str = "IN") -> List[str]:
    """Get today's trending searches from Google Trends."""
    try:
        from pytrends.request import TrendReq
        pytrend = TrendReq(hl="en-US", tz=330)
        trending = pytrend.trending_searches(pn="india" if geo == "IN" else "united_states")
        return [str(t) for t in trending[0].tolist()[:20]]
    except Exception as e:
        print(f"  ⚠ Google Trends fetch failed: {e}")
        return []


def filter_tech_trends(trends: List[str], extra_seeds: Optional[set] = None) -> List[str]:
    """Filter trending searches for AI/tech relevance."""
    seeds = _TECH_SEEDS | (extra_seeds or set())

    # Load seed phrases from config
    cfg = _load_trends_config()
    corpus_cfg = cfg.get("corpus_signals", {})
    if corpus_cfg.get("seed_phrases"):
        seeds.update(corpus_cfg["seed_phrases"])

    tech_trends = []
    for t in trends:
        t_lower = t.lower()
        if any(seed in t_lower for seed in seeds):
            tech_trends.append(t)

    return tech_trends


def enrich_trend_with_gemini(trend_keyword: str) -> Optional[Dict[str, Any]]:
    """Use Gemini to expand a trending keyword into a full post-ready dict."""
    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=(
                f"The keyword '{trend_keyword}' is trending on Google right now. "
                "Write a short AI/tech news post about it. Return ONLY valid JSON:\n"
                '{"topic": "Headline (max 80 chars)", '
                '"slides": ["Fact 1", "Fact 2", "Fact 3", "Fact 4"], '
                '"sources": [{"title": "Source", "url": "https://..."}], '
                '"hashtags": "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5"}'
            ))])],
            config=types.GenerateContentConfig(
                temperature=0.6,
                response_mime_type="application/json",
            ),
        )

        import json, re
        text = getattr(resp, "text", "") or ""
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group(0))
            data["content_source"] = "google_trends"
            return data
    except Exception as e:
        print(f"  ⚠ Gemini enrichment failed for '{trend_keyword}': {e}")

    return None


def pick_best_trend_topic() -> Optional[Dict[str, Any]]:
    """Fetch Google Trends, filter for tech, enrich the top one."""
    cfg = _load_trends_config()
    geo = cfg.get("geo", "IN")

    trends = fetch_trending_searches(geo)
    if not trends:
        return None

    tech = filter_tech_trends(trends)
    if not tech:
        # If no tech trends found, try the top 3 general trends with Gemini
        tech = trends[:3]

    for keyword in tech[:5]:
        result = enrich_trend_with_gemini(keyword)
        if result:
            return result
        time.sleep(1)

    return None
