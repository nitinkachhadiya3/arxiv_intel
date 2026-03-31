"""
Cricket Ingestor — fetches IPL 2026 live scores and news using Gemini Search Grounding.
"""
import os
import json
import logging
from typing import Any, Dict, Optional
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

def pick_best_cricket_topic() -> Optional[Dict[str, Any]]:
    """
    Fetch the latest IPL 2026 match summary or news using Gemini Google Search Grounding.
    Returns as a standard post-ready dict.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.error("GEMINI_API_KEY not found; skipping cricket ingestion.")
        return None

    client = genai.Client(api_key=api_key)
    
    # Using 3.1 Flash for "Creative Director" autonomy and grounding
    prompt = (
        "Search Google for a highly interesting, tactical, or unusual story from the latest IPL 2026 matches. "
        "IMPORTANT: Pick a unique story that isn't just a generic score. Look for specific player performance peaks, "
        "unusual tactical surprises, or venue-specific records that are trending NOW.\n\n"
        "DECIDE the best format for this story:\n"
        "1. 'SINGLE' - One high-impact summary with a powerful hero image.\n"
        "2. 'CAROUSEL' - A 5-slide breakdown using 'IMAGE' slides (visuals) and 'STATS' slides (data-heavy/text-only).\n\n"
        "Return EXCLUSIVELY a JSON object:\n"
        "{\n"
        "  \"post_type\": \"SINGLE|CAROUSEL\",\n"
        "  \"topic\": \"Engaging headline\",\n"
        "  \"slides\": [\n"
        "    {\"type\": \"IMAGE|STATS\", \"content\": \"The text for this slide\"}\n"
        "  ],\n"
        "  \"sources\": [{\"title\": \"Source Name\", \"url\": \"https://...\"}],\n"
        "  \"hashtags\": \"#IPL2026 #CricketStrategy...\",\n"
        "  \"content_source\": \"ipl_grounding\"\n"
        "}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        
        # Clean the response in case of markdown wrapping
        import re
        text = getattr(response, "text", "") or ""
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group(0))
            if data.get("topic"):
                data["content_source"] = "ipl_grounding"
                return data

    except Exception as e:
        logger.error(f"⚠ IPL grounding fetch failed: {e}")

    # Fallback to hardcoded sample if grounding fails during development
    return {
        "topic": "IPL 2026: The Strategic Powerplay Revolution",
        "slides": [
            "Teams are now prioritizing 'Death Over' specialists early in the Powerplay to disrupt momentum.",
            "Historical data shows matches are being won in the 10th-15th over consolidation phase.",
            "Key Player: Rashid Khan's economy rate remains the benchmark for T20 excellence.",
            "The upcoming MI vs GT clash will test the new two-bouncer-per-over rule impact."
        ],
        "sources": [{"title": "IPL News", "url": "https://www.iplt20.com"}],
        "hashtags": "#IPL2026 #CricketStrategy #MI #GT",
        "content_source": "fallback_cricket"
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(pick_best_cricket_topic(), indent=2))
