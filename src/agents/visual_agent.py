"""
VisualAgent — receives match context from DataAgent and decides:
  1. Which slides need a VISUAL (image) vs TEXT-ONLY (editorial background).
  2. Which Sports Visual World to assign to each visual slide.
  3. Builds a full 8k cinematic prompt for Gemini image generation.

This is the "Creative Director" in the multi-agent pipeline.
"""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple

# ── SPORTS VISUAL WORLDS (24 cricket-specific cinematic directions) ────────

SPORTS_WORLDS: List[Dict[str, Any]] = [
    {
        "id": "player_hero_portrait",
        "name": "Hero Player Portrait",
        "keywords": ["player", "batsman", "bowler", "allrounder", "captain", "spotlight",
                     "rohit", "kohli", "bumrah", "pandya", "dhoni", "maxwell", "siraj"],
        "prompt": (
            "Ultra-realistic 8k editorial portrait of a professional Indian cricket player in full IPL team kit. "
            "Intense focus in the eyes, realistic skin texture, sweat glistening under stadium floodlights. "
            "Background: blurred, glowing stadium crowd in team colors. "
            "Shot on Canon EOS R3, 85mm f/1.4, cinematic depth of field. "
            "Magazine cover quality — Widen your World / Sport Illustrated style. "
            "The jersey must show authentic team branding. NO cartoon. NO illustration. PURE REALISM."
        ),
        "mood": "intense, heroic, cinematic",
    },
    {
        "id": "batting_action",
        "name": "Batting Power Shot",
        "keywords": ["six", "four", "boundary", "batting", "shot", "cover drive", "pull shot", "sixer"],
        "prompt": (
            "Hyperrealistic 8k action photograph of a cricket batsman mid-swing, playing a massive six. "
            "Ball frozen in the air, bat impact blur, stadium crowd erupting behind them. "
            "Golden floodlight glow, dramatic motion blur on crowd. "
            "Shot on Sony A1, 400mm f/2.8, 1/4000s shutter speed. "
            "ESPN/Getty Sports Photography quality. Jersey details sharp and authentic."
        ),
        "mood": "explosive, kinetic, powerful",
    },
    {
        "id": "bowling_action",
        "name": "Bowling Delivery",
        "keywords": ["wicket", "yorker", "bouncer", "bowling", "delivery", "stumps", "caught", "lbw"],
        "prompt": (
            "Ultra-realistic 8k sports photograph of a fast bowler mid-delivery stride, "
            "arm at full extension, ball leaving the fingers. "
            "Stumps visible in background, batsman at the crease. "
            "Low angle, stadium lights creating dramatic rim lighting. "
            "Canon 1DX Mark III, 300mm, f/2.8. AP wire photo quality."
        ),
        "mood": "fierce, technical, dramatic",
    },
    {
        "id": "celebration_moment",
        "name": "Century/Wicket Celebration",
        "keywords": ["century", "hundred", "50", "five-wicket", "hat-trick", "celebration", "record",
                     "milestone", "achievement"],
        "prompt": (
            "8k hyperrealistic celebration photograph of a cricket player raising their bat/arm "
            "after achieving a milestone (century or wicket). "
            "Pure joy and emotion on their face — authentic human expression. "
            "Confetti or crowd crowd erupting in the background, team colors everywhere. "
            "Getty Images celebration quality, shot on Nikon Z9, 135mm."
        ),
        "mood": "joyful, triumphant, emotional",
    },
    {
        "id": "stadium_aerial_day",
        "name": "Stadium Aerial Day",
        "keywords": ["stadium", "venue", "ground", "pitch", "chinnaswamy", "wankhede", "eden",
                     "chepauk", "day match", "afternoon"],
        "prompt": (
            "Stunning 8k aerial drone photograph of a packed IPL cricket stadium during a daytime match. "
            "Perfect green turf with white pitch markings, 60,000+ crowd, "
            "surrounding city skyline visible in background. "
            "Golden afternoon light, deep blue sky. "
            "DJI Inspire 3 drone, Zenmuse X9-8K camera. Feels like an official IPL broadcast still."
        ),
        "mood": "grand, epic, nationwide scale",
    },
    {
        "id": "stadium_floodlit_night",
        "name": "Stadium at Night Under Floodlights",
        "keywords": ["night match", "floodlight", "evening", "night", "dew", "pink ball"],
        "prompt": (
            "Epic 8k wide-angle photograph of a cricket stadium at night under blazing floodlights. "
            "The entire 60,000-seat ground is packed, fans lit by the warm white floodlights. "
            "Pitch illuminated perfectly, players visible as tiny figures in the center. "
            "Deep blue sky, glowing halo around the lights. "
            "Feels like an official BCCI / Star Sports broadcast standard image."
        ),
        "mood": "electric, iconic, spectacular",
    },
    {
        "id": "crowd_wave",
        "name": "Crowd Energy Wave",
        "keywords": ["crowd", "fans", "supporters", "atmosphere", "wave", "chanting", "packed"],
        "prompt": (
            "8k action photograph of an erupting IPL stadium crowd. "
            "Thousands of fans on their feet, team colors — red, blue, yellow — everywhere. "
            "Flags waving, phones with flashlights on. "
            "Motion blur on the crowd to convey energy. "
            "Shot from pitch level looking up at the stands. "
            "Cinematic + sports photojournalism style."
        ),
        "mood": "passionate, collective, energy",
    },
    {
        "id": "fielding_dive",
        "name": "Spectacular Fielding Dive",
        "keywords": ["catch", "fielding", "dive", "boundary save", "run out", "direct hit", "stumping"],
        "prompt": (
            "Hyperrealistic 8k photograph of a cricket fielder diving full-length to take "
            "a stunning boundary catch or stop. "
            "Player parallel to the ground, ball in outstretched hand, grass/dust flying up. "
            "Stadium background in deep bokeh. "
            "1/8000s shutter speed, Nikon Z9, 500mm. World-class sports photojournalism."
        ),
        "mood": "athletic, breathtaking, reflexive",
    },
    {
        "id": "pitch_closeup",
        "name": "Pitch Detail Macro",
        "keywords": ["pitch", "surface", "spin", "bounce", "cracks", "conditions", "curator"],
        "prompt": (
            "Ultra-detailed 8k macro photograph of a cricket pitch surface mid-match. "
            "Cracked earth, worn batting crease marks, rough patches from spinner footmarks. "
            "Ball resting on the surface in the foreground. "
            "Golden-hour side lighting creating dramatic shadows across the texture. "
            "Technical, beautiful, tells the story of the match conditions."
        ),
        "mood": "tactical, detailed, strategic",
    },
    {
        "id": "dressing_room_intensity",
        "name": "Dressing Room Intensity",
        "keywords": ["team", "huddle", "strategy", "coaching", "captain", "team talk", "timeout"],
        "prompt": (
            "Cinematic 8k photograph of an IPL dressing room during the strategic timeout. "
            "Players in team kit gathered around the captain and coach, "
            "intense concentration on their faces, tactical diagram on whiteboard. "
            "Warm tungsten indoor lighting, handheld camera feel. "
            "Feels like an exclusive behind-the-scenes ESPN feature."
        ),
        "mood": "intense, strategic, intimate",
    },
    {
        "id": "trophy_glory",
        "name": "Trophy Lift Moment",
        "keywords": ["trophy", "win", "winner", "champion", "title", "ipl winner", "lifted"],
        "prompt": (
            "8k photograph of the IPL trophy being lifted by the winning captain "
            "under a shower of gold and silver confetti. "
            "Entire team celebrating behind, stadium in full celebration. "
            "Fireworks exploding in the background sky. "
            "Pure raw joy — tears, screams, hugs. "
            "Getty Images grand final photography quality."
        ),
        "mood": "glorious, euphoric, historic",
    },
    {
        "id": "run_chase_tension",
        "name": "Tense Run Chase",
        "keywords": ["run chase", "last over", "final over", "target", "needed", "required rate",
                     "nail-biting", "thriller"],
        "prompt": (
            "8k cinematic photograph of a batsman and batting partner at the crease "
            "in the final overs of a tense run chase. "
            "Close-up, both batsmen in conversation mid-pitch, stadium ablaze behind them. "
            "2-player environmental portrait, dramatic tension visible in their posture. "
            "Leica SL3, 50mm. Professional cricket photography quality."
        ),
        "mood": "tense, dramatic, edge-of-seat",
    },
    {
        "id": "impact_player_entry",
        "name": "Impact Player Walking Out",
        "keywords": ["impact player", "substitute", "walking out", "opening", "debut", "comeback"],
        "prompt": (
            "8k dramatic photograph of a cricket player walking out of the pavilion "
            "to bat, helmet in hand, crowd roaring. "
            "Long lens, player isolated against the bright green outfield. "
            "Natural stadium light, emotional crowd visible as a blur of color. "
            "Shot on Canon R5, 600mm f/4. Feels like a historic sporting moment."
        ),
        "mood": "determined, lone warrior, epic",
    },
    {
        "id": "umpire_decision",
        "name": "DRS / Umpire Drama",
        "keywords": ["drs", "umpire", "no-ball", "wide", "review", "decision", "controversy"],
        "prompt": (
            "8k sports photograph of the dramatic DRS review moment — "
            "umpire consulting the third umpire, players frozen around the wicket. "
            "Big screen showing the ball-tracking replay in the background. "
            "Multiple players gathered, tension palpable. "
            "Wide editorial environment shot, AP wire photo quality."
        ),
        "mood": "controversial, dramatic, forensic",
    },
    {
        "id": "powerplay_momentum",
        "name": "Powerplay Carnage",
        "keywords": ["powerplay", "first 6 overs", "pp", "opening", "six in powerplay"],
        "prompt": (
            "8k action shot of a batsman launching a massive six during the first powerplay. "
            "Ball soaring high, fielders jumping but unable to reach, packed crowd going wild. "
            "Golden light, fast shutter, frozen peak action. "
            "Sports Illustrated impact photograph style — "
            "the most dramatic possible moment in those 6 overs."
        ),
        "mood": "explosive, dominant, fearless",
    },
    {
        "id": "fast_bowling_duo",
        "name": "Pace Duo Partnership",
        "keywords": ["pace", "seam", "fast bowling", "duo", "express pace", "speed", "140", "150kph"],
        "prompt": (
            "8k cinematic split-perspective photograph of two pace bowlers "
            "running in from opposite ends — stadium in background. "
            "Speed-gun reading visible on screen (145+ km/h). "
            "Both players mid-action, intense expressions, authentic team kit. "
            "ESPN broadcast quality composition."
        ),
        "mood": "fearsome, aggressive, fast",
    },
    {
        "id": "spin_web",
        "name": "Spin Bowling Deception",
        "keywords": ["spin", "spinner", "googly", "leg spin", "off spin", "wrist spin", "flight", "turn"],
        "prompt": (
            "8k close-up photograph of a spinner mid-delivery, "
            "fingers visible curling over the ball with extreme precision. "
            "Ball released, batsman's footwork visible in the background. "
            "Macro detail of the grip, seam orientation sharp. "
            "Soft stadium lights, technical beauty shot."
        ),
        "mood": "subtle, deceptive, technical",
    },
    {
        "id": "broadcast_stats_board",
        "name": "Broadcast Score Screen",
        "keywords": ["scorecard", "score", "update", "stat", "data", "over", "rr", "rrr"],
        "prompt": (
            "8k photograph of the giant LED scoreboard above the stadium stands "
            "showing the live match score, required run rate, and target. "
            "Stadium crowd visible below the screen. "
            "Neon and LED glow reflecting on nearby surfaces. "
            "Editorial broadcast journalism quality."
        ),
        "mood": "analytical, live, real-time",
    },
    {
        "id": "golden_ticket_fans",
        "name": "Fan Zone Energy",
        "keywords": ["fans", "supporters", "jersey", "painted face", "team colors", "fan zone"],
        "prompt": (
            "8k crowd portrait of die-hard IPL fans in the stands. "
            "Faces painted in team colors, jerseys, flags, homemade banners. "
            "Laughing, chanting, jumping. Real human expressions of joy and passion. "
            "Shot from within the crowd at eye-level, wide-angle 24mm. "
            "Feels like a National Geographic feature on Indian cricket culture."
        ),
        "mood": "cultural, passionate, authentic",
    },
    {
        "id": "sunset_over_pavilion",
        "name": "Pavilion at Dusk",
        "keywords": ["pavilion", "dusk", "sunset", "match start", "sunset", "pre-match"],
        "prompt": (
            "8k architectural wide shot of the cricket pavilion and ground at dusk, "
            "just as the floodlights begin to come on. "
            "Warm orange sky transitioning to deep blue, silhouettes of players on the outfield. "
            "Perfect symmetry of the ground. "
            "Fine art sports photography — feels like a cricket calendar shot."
        ),
        "mood": "majestic, transitional, poetic",
    },
    {
        "id": "wicket_stumps_shattered",
        "name": "Stumps Exploding",
        "keywords": ["bowled", "stumps", "bails", "shattered", "knocked", "castle"],
        "prompt": (
            "8k hyper-slow-motion style photograph of stumps being shattered and bails flying. "
            "Ball frozen mid-trajectory having just beaten the bat. "
            "Batsman's dejected expression behind. "
            "Low angle, inch above the pitch surface, dramatic perspective. "
            "High-speed photography quality — 1/8000s, Nikon Z9."
        ),
        "mood": "devastating, dramatic, decisive",
    },
    {
        "id": "stat_card_data_viz",
        "name": "Editorial Stats Data Visual",
        "keywords": ["stats", "record", "numbers", "analysis", "comparison", "head-to-head", "history"],
        "prompt": (
            "8k clean editorial flat-lay: a cricket ball, wooden stump, and a "
            "printed stats sheet on a natural surface. "
            "Cinematic overhead shot, warm side-lighting creating shadows. "
            "Minimalist sports editorial for a premium publication. "
            "No screens. Physical objects only — tactile and premium."
        ),
        "mood": "analytical, premium, editorial",
    },
    {
        "id": "match_eve_practice",
        "name": "Training Session Drama",
        "keywords": ["practice", "nets", "training", "warm-up", "session", "prep"],
        "prompt": (
            "8k candid sports photograph of an IPL player at the nets the evening before a big match. "
            "Sweating intensely, helmet visor up, intense concentration. "
            "Indoor practice net lights casting dramatic shadows. "
            "Behind-the-scenes ESPN feature visual quality."
        ),
        "mood": "raw, prepared, honest",
    },
    {
        "id": "legacy_moment",
        "name": "Historic Legacy Moment",
        "keywords": ["legend", "legacy", "all-time", "greatest", "history", "historic", "era-defining"],
        "prompt": (
            "8k cinematic portrait of a veteran cricket legend standing on the outfield "
            "at sunset, stadium empty behind them, looking at the empty stands. "
            "Reflective, emotional, the weight of a career on their shoulders. "
            "Hasselblad H6D, 80mm, f/2 — magazine cover quality. "
            "Tells an entire story with a single frame."
        ),
        "mood": "reflective, timeless, legendary",
    },
]


# ── Semantic keyword → world mapping ─────────────────────────────────────

def _build_keyword_map() -> Dict[str, str]:
    """Reverse-index SPORTS_WORLDS by keywords for fast lookup."""
    idx: Dict[str, str] = {}
    for world in SPORTS_WORLDS:
        for kw in world.get("keywords", []):
            idx[kw.lower()] = world["id"]
    return idx


_KEYWORD_MAP = _build_keyword_map()

# Text-only slide templates (no Gemini image generation needed)
TEXT_ONLY_WORLDS = {"stat_card_data_viz", "broadcast_stats_board"}


class VisualAgent:
    """
    Creative Director Agent.

    Given the match context from DataAgent, decides for each slide:
    - Should it have an image? (visual_flag = True/False)
    - Which Sports Visual World fits best?
    - What is the full 8k cinematic image prompt?
    """

    def __init__(self):
        self._rng = random.Random()

    def decide_slide_plan(
        self, match_data: Dict[str, Any], slide_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Create a slide plan: list of dicts with keys:
          - slide_index (1-based)
          - visual_flag (bool)
          - world_id (str)
          - world_name (str)
          - image_prompt (str)
          - scene_hint (str)
        """
        post_type = match_data.get("post_type_suggestion", "SCORE_UPDATE")
        hero = match_data.get("hero_player", {})
        moments = match_data.get("trending_moments", [])
        records = match_data.get("records_broken", [])
        phase = match_data.get("match_phase", "")
        # Use the query hint if present for keyword-based world selection
        query_hint = match_data.get("_query", "").lower()

        # Determine hook world from query keywords
        hook_world = self._semantic_world_from_text(query_hint or post_type)

        plan = []
        for i in range(1, slide_count + 1):
            visual_flag, world_id, scene_hint = self._decide_for_slide(
                slide_idx=i,
                total=slide_count,
                post_type=post_type,
                hero=hero,
                moments=moments,
                records=records,
                match_data=match_data,
                hook_world=hook_world,
            )

            world = next((w for w in SPORTS_WORLDS if w["id"] == world_id), SPORTS_WORLDS[0])
            image_prompt = self._build_image_prompt(world, scene_hint, match_data) if visual_flag else ""

            plan.append({
                "slide_index": i,
                "visual_flag": visual_flag,
                "world_id": world_id,
                "world_name": world["name"],
                "image_prompt": image_prompt,
                "scene_hint": scene_hint,
            })

        return plan

    def _semantic_world_from_text(self, text: str) -> str:
        """Find the best matching Sports World ID from free text."""
        text_lower = text.lower()
        for kw, wid in _KEYWORD_MAP.items():
            if kw in text_lower:
                return wid
        return "player_hero_portrait"  # default hero portrait

    def _decide_for_slide(
        self, slide_idx: int, total: int,
        post_type: str, hero: Dict, moments: List[str],
        match_data: Dict, records: List[str] = None,
        hook_world: str = "player_hero_portrait",
    ) -> Tuple[bool, str, str]:
        """
        Decide visual_flag, world_id, and scene_hint for a single slide.
        Slide 1 → uses the semantic hook_world from the query (always visual)
        Slide 2 → text-only data (score / stats)
        Slide 3 → moment-keyword visual or text-only
        Slide 4 → hero player action (batting/bowling)
        Slide 5 → crowd energy CTA
        """
        records = records or []
        venue = match_data.get("venue", "IPL stadium")
        score = match_data.get("current_score", {}).get("team", "")
        hero_name = hero.get("name", "the star player")
        hero_role = hero.get("role", "Batsman")

        if slide_idx == 1:
            # Hook: use the query-derived semantic world
            scene_map = {
                "player_hero_portrait": (
                    f"Ultra-close portrait of {hero_name} in full IPL kit, "
                    f"stadium floodlights behind, intense expression, winning look"
                ),
                "batting_action": (
                    f"{hero_name} smashing a massive six at {venue}, "
                    f"crowd exploding in the stands behind"
                ),
                "bowling_action": (
                    f"{hero_name} mid-delivery stride, fierce expression, "
                    f"batsman at the crease, stadium roaring"
                ),
                "celebration_moment": (
                    f"{hero_name} raising bat/fist after milestone — "
                    f"crowd and teammates erupting around them"
                ),
                "trophy_glory": (
                    f"IPL 2026 trophy being lifted at {venue}, "
                    f"fireworks and confetti raining down"
                ),
                "run_chase_tension": (
                    f"Two batsmen mid-pitch conference in the final over at {venue}, "
                    f"scoreboard showing 12 needed off 6 balls"
                ),
                "stadium_aerial_day": (
                    f"Aerial shot of {venue}, packed 60,000 seat stadium, "
                    f"match in full swing, golden daylight"
                ),
                "stadium_floodlit_night": (
                    f"Wide floodlit night shot of {venue}, "
                    f"blaze of lights, crowd fully charged"
                ),
                "wicket_stumps_shattered": (
                    f"Stumps flying and bails exploding at {venue}, "
                    f"bowler wheeling away in celebration"
                ),
                "powerplay_momentum": (
                    f"Batsman launching a towering six in the powerplay at {venue}, "
                    f"fielder leaping but ball clearing the rope"
                ),
                "crowd_wave": (
                    f"Stadium crowd doing a massive wave at {venue}, "
                    f"entire stands on their feet"
                ),
                "fielding_dive": (
                    f"Outfielder diving full-length to save a boundary at {venue}, "
                    f"grass and dust flying, crowd in disbelief"
                ),
            }
            hint = scene_map.get(hook_world, (
                f"{hero_name} on the field at {venue}, match in progress, "
                f"crowd electric behind"
            ))
            return True, hook_world, hint

        elif slide_idx == 2:
            # Data — always text-only
            return False, "stat_card_data_viz", f"Live Score: {score}"

        elif slide_idx == 3:
            # Trending moment — visual if action-keyword matched
            moment_text = (records[0] if records else "") or (moments[0] if moments else "Key match moment")
            for kw, wid in _KEYWORD_MAP.items():
                if kw in moment_text.lower() and wid not in TEXT_ONLY_WORLDS:
                    return True, wid, moment_text
            return False, "stat_card_data_viz", moment_text

        elif slide_idx == 4:
            # Key performer action
            world_id = "batting_action" if hero_role == "Batsman" else "bowling_action"
            action = "driving the ball past mid-off" if hero_role == "Batsman" else "bowling a toe-crushing yorker"
            return True, world_id, f"{hero_name} {action} at {venue}"

        else:
            # Final — crowd energy + hashtag CTA
            return True, "crowd_wave", (
                f"Packed stands at {venue} going absolutely wild, "
                f"team colors everywhere, electric final-over atmosphere"
            )


    def _build_image_prompt(
        self, world: Dict[str, Any], scene_hint: str, match_data: Dict
    ) -> str:
        """
        Combine world cinematic template + scene-specific hint + composition rules.
        """
        venue = match_data.get("venue", "an IPL stadium")
        return f"""Scene: {scene_hint}
Venue: {venue}

CINEMATIC VISUAL DIRECTION:
{world['prompt']}

Mood: {world['mood']}

COMPOSITION RULE: Main action in the upper 65% of the frame.
Bottom 30% must be dark and relatively clean for text overlay.

OUTPUT: Ultra-realistic 8k sports photograph. NOT a cartoon, NOT an illustration.
Looks like a professional ESPN / Getty Images sports photo from IPL 2026.
Authentic player jerseys, real stadium environment, no generic stock imagery."""

    @staticmethod
    def get_world_by_keyword(keyword: str) -> Optional[Dict[str, Any]]:
        wid = _KEYWORD_MAP.get(keyword.lower())
        if wid:
            return next((w for w in SPORTS_WORLDS if w["id"] == wid), None)
        return None
