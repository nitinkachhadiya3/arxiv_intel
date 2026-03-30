"""
Unified Topic Picker — rotates across 5 content sources:

  1. RSS Feed (TechCrunch / The Verge / Ars Technica)
  2. HuggingFace Paper
  3. Google Trends + Gemini enrichment
  4. HuggingFace Model/Space
  5. Gemini Fresh News

Tracks rotation state in output/source_rotation.json.
Prevents duplicate topics via output/posted_topics.json (48h cooldown).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional


# Source rotation order
_SOURCE_ORDER = [
    "rss",
    "hf_paper",
    "google_trends",
    "hf_model",
    "gemini_fresh",
]

_ROTATION_FILE = Path("output/source_rotation.json")
_POSTED_FILE = Path("output/posted_topics.json")
_COOLDOWN_HOURS = 48


def _load_json(path: Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _save_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_next_source() -> str:
    """Get the next source in rotation."""
    state = _load_json(_ROTATION_FILE) or {"index": -1}
    idx = (state.get("index", -1) + 1) % len(_SOURCE_ORDER)
    return _SOURCE_ORDER[idx]


def _advance_rotation(source_used: str):
    """Save the rotation state after successfully picking a topic."""
    try:
        idx = _SOURCE_ORDER.index(source_used)
    except ValueError:
        idx = 0
    _save_json(_ROTATION_FILE, {
        "index": idx,
        "last_source": source_used,
        "last_used_at": time.time(),
    })


def _is_duplicate(topic: str) -> bool:
    """Check if a topic was posted within the cooldown window."""
    posted = _load_json(_POSTED_FILE) or []
    if not isinstance(posted, list):
        return False

    cutoff = time.time() - (_COOLDOWN_HOURS * 3600)
    
    # Common tech/news stopwords to ignore for better similarity matching
    _STOP_WORDS = {"a", "an", "the", "in", "on", "at", "to", "for", "with", "by", "is", "are", "was", "were", "and", "or", "but", "of"}
    
    topic_words = {w for w in re.sub(r"[^a-z0-9 ]", "", topic.lower()).split() if w not in _STOP_WORDS}

    for entry in posted:
        if entry.get("ts", 0) < cutoff:
            continue
        old_topic = entry.get("topic", "").lower()
        old_words = {w for w in re.sub(r"[^a-z0-9 ]", "", old_topic).split() if w not in _STOP_WORDS}
        
        if not topic_words or not old_words:
            # If headlines are too short, skip similarity and check exact match
            if topic.strip().lower() == old_topic.strip():
                return True
            continue
            
        # Jaccard similarity on non-stopwords
        overlap = len(topic_words & old_words) / max(len(topic_words | old_words), 1)
        # 0.45 is a safer threshold for "nearly identical" when ignoring stopwords
        if overlap > 0.45:
            return True
    return False


def _record_posted(topic: str, source: str):
    """Record a topic as posted."""
    posted = _load_json(_POSTED_FILE) or []
    if not isinstance(posted, list):
        posted = []
    posted.append({"topic": topic, "source": source, "ts": time.time()})
    # Keep only last 50
    _save_json(_POSTED_FILE, posted[-50:])


def _fetch_from_source(source: str) -> Optional[Dict[str, Any]]:
    """Fetch a topic from a specific source."""
    print(f"  📡 Trying source: {source}")

    if source == "rss":
        from src.ingestion.rss_ingestor import pick_best_rss_topic
        return pick_best_rss_topic()

    elif source == "hf_paper":
        from src.ingestion.hf_ingestor import pick_best_hf_topic
        return pick_best_hf_topic("paper")

    elif source == "google_trends":
        from src.ingestion.google_trends_ingestor import pick_best_trend_topic
        return pick_best_trend_topic()

    elif source in ("hf_model", "hf_space"):
        from src.ingestion.hf_ingestor import pick_best_hf_topic
        subtype = "model" if source == "hf_model" else "space"
        return pick_best_hf_topic(subtype)

    elif source == "gemini_fresh":
        return _fetch_gemini_fresh()

    return None


def _fetch_gemini_fresh() -> Optional[Dict[str, Any]]:
    """Fetch a fresh topic via Gemini (the original method)."""
    try:
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",  # Upgraded to Flash 3 model
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=(
                "You are a tech news editor. Return ONLY valid JSON with the latest, "
                "most interesting AI or technology news from TODAY. Pick a unique story. "
                "Format:\n"
                '{"topic": "One-line headline (max 80 chars)", '
                '"slides": ["Slide 1 fact...", "Slide 2 fact...", "Slide 3 fact...", "Slide 4 fact..."], '
                '"sources": [{"title": "Source name", "url": "https://..."}], '
                '"hashtags": "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5"}'
            ))])],
            config=types.GenerateContentConfig(
                temperature=0.8,
                response_mime_type="application/json",
            ),
        )

        import re as _re
        text = getattr(resp, "text", "") or ""
        m = _re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group(0))
            data["content_source"] = "gemini_fresh"
            return data
    except Exception as e:
        print(f"  ⚠ Gemini fresh fetch failed: {e}")

    return None


def pick_fresh_topic() -> Dict[str, Any]:
    """
    Pick a fresh topic using the rotation system.
    Tries the next source in rotation, falls back through others.
    Returns a post-ready dict.
    """
    primary = get_next_source()
    print(f"🔄 Source rotation: next = {primary}")

    # Build fallback chain starting from the primary
    try:
        start_idx = _SOURCE_ORDER.index(primary)
    except ValueError:
        start_idx = 0

    fallback_chain = []
    for i in range(len(_SOURCE_ORDER)):
        src = _SOURCE_ORDER[(start_idx + i) % len(_SOURCE_ORDER)]
        fallback_chain.append(src)

    for source in fallback_chain:
        try:
            result = _fetch_from_source(source)
            if result and result.get("topic"):
                topic = result["topic"]
                if _is_duplicate(topic):
                    print(f"  ⏭ Duplicate topic skipped: {topic[:60]}...")
                    continue
                # Success
                result["content_source"] = result.get("content_source", source)
                _advance_rotation(source)
                _record_posted(topic, source)
                print(f"  ✅ Topic from {source}: {topic}")
                return result
        except Exception as e:
            print(f"  ⚠ Source {source} failed: {e}")
            continue

    # Ultimate fallback
    print("  ⚠ All sources failed, using hardcoded fallback")
    fallback = {
        "topic": "AI Industry Reaches $2.5 Trillion in Global Spending",
        "slides": [
            "Global AI spending has reached $2.52 trillion in 2026, a 44% increase from 2025.",
            "88% of companies now report using AI in at least one business function.",
            "Agentic AI is the fastest-growing segment, with Gartner predicting 40% enterprise adoption.",
            "The cost of running AI systems continues to fall, making powerful technology accessible to startups."
        ],
        "sources": [{"title": "Industry Reports", "url": "https://buildez.ai"}],
        "hashtags": "#AI #TechNews #Innovation #FutureOfAI #ArxivIntel",
        "content_source": "fallback",
    }
    _advance_rotation("gemini_fresh")
    return fallback
