"""
DataAgent — fetches live IPL match data, player stats, and
trending hashtags using Gemini Google Search Grounding.

It acts as the "intelligence gatherer" in the multi-agent pipeline.
Other agents query it via its public API; it caches results so we
don't hammer the search API on every slide.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Simple in-process TTL cache ───────────────────────────────────────────
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 300  # 5 minutes

# IPL 2026 player roster (used as a fallback keyword bank)
IPL_PLAYERS = {
    "rcb":  ["Virat Kohli", "Faf du Plessis", "Glenn Maxwell", "Mohammed Siraj",
              "Dinesh Karthik", "Cameron Green", "Harshal Patel"],
    "mi":   ["Rohit Sharma", "Jasprit Bumrah", "Hardik Pandya", "Suryakumar Yadav",
              "Tim David", "Tilak Varma", "Ishan Kishan"],
    "csk":  ["MS Dhoni", "Ruturaj Gaikwad", "Devon Conway", "Deepak Chahar",
              "Ravindra Jadeja", "Shivam Dube"],
    "dc":   ["David Warner", "Prithvi Shaw", "Axar Patel", "Anrich Nortje"],
    "kkr":  ["Shreyas Iyer", "Andre Russell", "Sunil Narine", "Nitish Rana",
              "Varun Chakravarthy"],
    "lsg":  ["KL Rahul", "Quinton de Kock", "Marcus Stoinis", "Ravi Bishnoi"],
    "gt":   ["Shubman Gill", "Hardik Pandya", "Mohammed Shami", "Rashid Khan",
              "David Miller"],
    "pbks": ["Shikhar Dhawan", "Liam Livingstone", "Arshdeep Singh", "Sam Curran"],
    "rr":   ["Sanju Samson", "Jos Buttler", "Yuzvendra Chahal", "Shimron Hetmyer"],
    "srh":  ["Abhishek Sharma", "Heinrich Klaasen", "Pat Cummins", "Bhuvneshwar Kumar",
              "Aiden Markram"],
}

TEAM_HASHTAGS = {
    "rcb":  ["#RCB", "#PlayBold", "#RoyalChallengersBangalore", "#ViratKohli"],
    "mi":   ["#MI", "#MumbaiIndians", "#RohitSharma", "#Paltan"],
    "csk":  ["#CSK", "#ChennaiSuperKings", "#WhistlePodu", "#Thala"],
    "dc":   ["#DC", "#DelhiCapitals", "#DilDilli"],
    "kkr":  ["#KKR", "#KolkataKnightRiders", "#KorboLorboJeetbo"],
    "lsg":  ["#LSG", "#LucknowSuperGiants"],
    "gt":   ["#GT", "#GujaratTitans", "#AavaDe"],
    "pbks": ["#PBKS", "#PunjabKings", "#SaddaPunjab"],
    "rr":   ["#RR", "#RajasthanRoyals", "#HallaBol"],
    "srh":  ["#SRH", "#SunrisersHyderabad", "#OrangeArmy"],
}

BASE_CRICKET_HASHTAGS = [
    "#IPL2026", "#IPL", "#Cricket", "#T20", "#IndianPremierLeague",
    "#CricketTwitter", "#CricketLovers", "#T20Cricket", "#IPLMatch",
    "#CricketFans", "#BCCI", "#IPLHighlights", "#CricketIsLife",
    "#SixHitter", "#MatchDay",
]


def _get_client():
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


class DataAgent:
    """
    Autonomous Data Intelligence Agent.

    Responsibilities:
    - Fetch live match context via Gemini Search Grounding
    - Extract trending topics and hashtags
    - Identify key players, moments, and records
    - Cache results to avoid redundant API calls
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def fetch_live_match(self, query: str = "IPL 2026 today match") -> Dict[str, Any]:
        """
        Pull the richest, most recent IPL match context.
        Returns a structured dict for downstream agents.
        """
        cache_key = f"match_{query}"
        cached = _CACHE.get(cache_key)
        if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
            logger.info("DataAgent: cache hit for '%s'", query)
            return cached["data"]

        logger.info("DataAgent: fetching live match data…")
        try:
            client = _get_client()
            from google.genai import types

            prompt = f"""
You are an expert IPL data journalist. Search for the MOST RECENT news about: "{query}".

Extract and return a rich JSON object with these exact keys:
{{
  "match_title": "Team A vs Team B – Match N, Venue, Date",
  "teams": {{"team1": "Full name + short code", "team2": "Full name + short code"}},
  "current_score": {{"team": "score/overs", "batting_team": "name"}},
  "key_performers": [
    {{"name": "Player", "team": "short", "stat": "45 off 28", "role": "Batsman/Bowler"}}
  ],
  "records_broken": ["Record 1", "Record 2"],
  "trending_moments": ["Moment 1 in one line", "Moment 2"],
  "match_phase": "Powerplay|Middle Overs|Death Overs|Post-Match",
  "venue": "Stadium name, City",
  "crowd_mood": "Electric|Tense|Celebratory|Disappointed",
  "trending_hashtags": ["#Tag1", "#Tag2"],
  "post_type_suggestion": "PLAYER_SPOTLIGHT|SCORE_UPDATE|RECORD_BREAKER|MATCH_PREVIEW|MATCH_REVIEW",
  "hero_player": {{"name": "Player", "team": "short", "jersey_number": "N", "role": "Batsman"}},
  "insight_text": "One powerful insight a commentator would say right now"
}}
Return ONLY the JSON object, no other text.
"""
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    response_mime_type="application/json",
                    temperature=0.4,
                ),
            )
            text = getattr(resp, "text", "") or ""
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                data = json.loads(m.group(0))
                _CACHE[cache_key] = {"data": data, "ts": time.time()}
                logger.info("DataAgent: match data fetched OK – %s", data.get("match_title"))
                return data
        except Exception as exc:
            logger.warning("DataAgent: live fetch failed – %s", exc)

        return self._fallback_match()

    def build_hashtag_block(self, match_data: Dict[str, Any]) -> List[str]:
        """
        Build a rich, 20+ hashtag block from match context.
        """
        tags: List[str] = list(BASE_CRICKET_HASHTAGS)

        # Team hashtags
        for team_key in ["team1", "team2"]:
            code = (match_data.get("teams", {}).get(team_key, "")).lower()
            for k, v in TEAM_HASHTAGS.items():
                if k in code:
                    tags.extend(v)
                    break

        # Player hashtags
        for performer in match_data.get("key_performers", []):
            name = performer.get("name", "")
            if name:
                tag = "#" + re.sub(r"\s+", "", name)
                tags.append(tag)

        hero = match_data.get("hero_player", {}).get("name", "")
        if hero:
            tags.append("#" + re.sub(r"\s+", "", hero))

        # Trending tags from API
        tags.extend(match_data.get("trending_hashtags", []))

        # Deduplicate while preserving order
        seen, unique = set(), []
        for t in tags:
            tl = t.lower()
            if tl not in seen:
                seen.add(tl)
                unique.append(t)

        return unique[:25]  # cap at 25

    def get_player_roster(self, team_code: str) -> List[str]:
        return IPL_PLAYERS.get(team_code.lower(), [])

    @staticmethod
    def _fallback_match() -> Dict[str, Any]:
        """Realistic hardcoded fallback for offline development."""
        return {
            "match_title": "RCB vs MI – Match 14, M. Chinnaswamy Stadium, 2026",
            "teams": {"team1": "Royal Challengers Bangalore (RCB)", "team2": "Mumbai Indians (MI)"},
            "current_score": {"team": "MI: 185/4 (18.3 ov)", "batting_team": "Mumbai Indians"},
            "key_performers": [
                {"name": "Rohit Sharma", "team": "MI", "stat": "72 off 48", "role": "Batsman"},
                {"name": "Jasprit Bumrah", "team": "MI", "stat": "2/24 (4 ov)", "role": "Bowler"},
                {"name": "Virat Kohli", "team": "RCB", "stat": "55 off 38", "role": "Batsman"},
            ],
            "records_broken": [
                "Rohit Sharma surpasses 7000 IPL runs — only the 2nd player ever",
                "M. Chinnaswamy highest first-innings total this season",
            ],
            "trending_moments": [
                "Bumrah's unplayable yorker dismissed Maxwell for a duck in the 3rd over",
                "Kohli hits back-to-back sixes off Bumrah — crowd goes berserk",
                "Hardik Pandya takes a stunning reflex catch at mid-off",
            ],
            "match_phase": "Death Overs",
            "venue": "M. Chinnaswamy Stadium, Bengaluru",
            "crowd_mood": "Electric",
            "trending_hashtags": [
                "#RCBvsMI", "#KingKohli", "#RohitSharma7000", "#BumrahBack",
                "#IPLFinal", "#CricketTwitter",
            ],
            "post_type_suggestion": "RECORD_BREAKER",
            "hero_player": {"name": "Rohit Sharma", "team": "MI", "jersey_number": "45", "role": "Batsman"},
            "insight_text": "Rohit Sharma is rewriting T20 batting history at the age of 39 — pure class.",
        }
