"""
Content strategist: classify format, pick hooks, and plan slides before image generation.

Produces a JSON-serializable brief compatible with `try_render_gemini_carousel(..., story_brief=...)`.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from src.utils.config import AppConfig
from src.utils.gemini_models import gemini_model_candidates, is_gemini_model_unavailable_error
from src.utils.logger import get_logger, log_stage
from src.content.persona_loader import load_persona

_LOG = get_logger("content.story_brief")

_MAX_SLIDES = int(os.getenv("STORY_MAX_SLIDES", "6"))
_STRATEGIST = (os.getenv("STORY_STRATEGIST_ENABLED", "1") or "1").strip().lower() not in ("0", "false", "no")


def story_strategist_enabled() -> bool:
    return _STRATEGIST


def _brand_context() -> tuple[str, str]:
    brand = (os.getenv("BRAND_NAME") or "ArXiv Intel").strip() or "ArXiv Intel"
    category = (os.getenv("CONTENT_CATEGORY") or "technology").strip() or "technology"
    return brand, category


def _story_system_prompt(persona: dict = None) -> str:
    brand, category = _brand_context()
    
    image_style_block = ""
    custom_rules = ""
    if persona:
        if "carousel_rules" in persona:
            custom_rules = "\n".join(f"- CUSTOM RULE: {r}" for r in persona["carousel_rules"]) + "\n"
        if "logical_constraints" in persona:
            lc = persona["logical_constraints"]
            custom_rules += "\nCRITICAL DATA LOGIC CONSTRAINTS:\n" + "\n".join(f"- {c}" for c in lc) + "\n"

        if "image_generation" in persona:
            vs = persona["image_generation"].get("visual_style", "")
            gr = persona["image_generation"].get("guardrails", [])
            gr_text = "\n".join(f"  * {g}" for g in gr)
            image_style_block = f"IMAGE GENERATION RULES for 'visual_hint':\n{vs}\nGuardrails:\n{gr_text}\n"

        if "story_strategist" in persona:
            sys_role = persona["story_strategist"].get("system_role", f"You are the editorial strategist for a premium {category}-news Instagram brand.")
            primary_focus = persona["story_strategist"].get("primary_focus", "")
            role_block = f'{sys_role} Brand name: "{brand}".\nPrimary focus: {primary_focus}\n\n'
        else:
            role_block = f'You are the editorial strategist for "{brand}", a premium {category}-news Instagram brand.\n\n'
    else:
        role_block = f'You are the editorial strategist for "{brand}", a premium {category}-news Instagram brand.\n\n'

    return (
        f'{role_block}'
        "Return ONLY valid JSON (no markdown) with this shape:\n"
        "{\n"
        '  "content_type": "single" | "carousel",\n'
        '  "content_visual_type": "founder" | "product" | "infrastructure" | "news" | "insight",\n'
        '  "reason": "one sentence",\n'
        '  "content_depth": "low" | "medium" | "high",\n'
        '  "audience_angle": "curiosity" | "opportunity" | "risk" | "policy",\n'
        '  "primary_claim": "one factual sentence, no hype",\n'
        '  "hook_candidates": ["4-5 short option strings"],\n'
        '  "hook_selected": "best hook from candidates; punchy, credible, max ~12 words",\n'
        '  "all_in_one_datapoint_1": "► Short supporting fact 1 (max ~55 chars)",\n'
        '  "all_in_one_datapoint_2": "► Short supporting fact 2 (max ~55 chars)",\n'
        '  "slide_plan": [\n'
        "    {\n"
        '      "role": "hook | context | insight | data | outlook | cta",\n'
        '      "headline": "ALL CAPS one line for overlay, max ~90 chars",\n'
        '      "one_idea": "internal note, one sentence",\n'
        '      "visual_hint": "Describe a REAL-WORLD photographic scene for this slide. Think like a photo editor assigning a photographer. Describe the SETTING (office, city, lab, conference, street), SUBJECT (person, building, object, landscape), LIGHTING (natural, golden hour, studio), and MOOD. NEVER suggest: glowing neural networks, electrical wires, circuit boards, holographic UI, neon cyberpunk, or generic 3D tech renders. The image must look like professional editorial photography, not AI art."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "content_visual_type rules: Classify the topic semantically:\n"
        "- 'founder' = story about a CEO, founder, or tech leader (human-centric visuals)\n"
        "- 'product' = new product launch, feature release, AI model (futuristic tech visuals)\n"
        "- 'infrastructure' = data centers, chips, servers, cloud, networks (industrial/architectural)\n"
        "- 'news' = general breaking news, policy, regulation, deals (documentary/real-world)\n"
        "- 'insight' = research paper, study, benchmark, analysis (minimal/abstract/data-viz)\n\n"
        f"{image_style_block}\n"
        "Rules:\n"
        f"{custom_rules}"
        '- If ONE core fact or simple update → content_type "single", slide_plan length 1. Still fill datapoint_1 and datapoint_2 from the story.\n'
        '- If multi-beat explainer (3+ distinct ideas) → "carousel", slide_plan 4-6 slides max. Slide 1 MUST work alone: headline + two datapoints already chosen; slide_plan[0].headline should match hook_selected tone.\n'
        '- Slide 2+ headline is ONE idea each, short ALL CAPS fragments (not paragraphs).\n'
        "- Never invent events or casualties. No clickbait lies. Hooks can be curiosity but must be defensible from the sources.\n"
        "- STATISTICAL INTEGRITY: Do NOT invent specific numbers (e.g., '185 runs in powerplay') that are logically impossible or contradict the sources. If a number is in 'Sources', use it; otherwise, provide tactical analysts' qualitative context instead of fake numbers.\n"
    )


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    s = text.strip()
    m = re.search(r"\{[\s\S]*\}\s*$", s)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def fallback_story_brief(post: Dict[str, Any]) -> Dict[str, Any]:
    """Heuristic brief when Gemini text is unavailable."""
    topic = str(post.get("topic") or "Tech update")
    slides = list(post.get("slides") or [])
    posters = list(post.get("poster_headlines") or [])
    visuals = list(post.get("visual_prompts") or [])
    cover = str(post.get("cover_headline") or (posters[0] if posters else topic))[:200]

    depth = "high" if len(slides) > 4 else ("medium" if len(slides) > 2 else "low")
    single = len(slides) <= 2 and depth == "low"
    content_type = "single" if single else "carousel"

    roles = ["hook", "context", "insight", "data", "outlook", "cta"]
    plan: List[Dict[str, Any]] = []
    n = min(_MAX_SLIDES, max(1, len(posters) or len(slides) or 1))
    for i in range(n):
        hl = posters[i] if i < len(posters) else (slides[i][:100] + "…" if i < len(slides) and len(slides[i]) > 100 else (slides[i] if i < len(slides) else cover))
        hint = visuals[i] if i < len(visuals) else "Symbolic tech skyline at blue hour, cyan edge lights, no text."
        plan.append(
            {
                "role": roles[i] if i < len(roles) else "detail",
                "headline": hl.upper()[:95],
                "one_idea": hl[:200],
                "visual_hint": hint[:300],
            }
        )

    d1 = "► " + (slides[1][:52] + "…" if len(slides) > 1 and len(slides[1]) > 52 else (slides[1] if len(slides) > 1 else "Key timing and scope."))
    d2 = "► " + (slides[2][:52] + "…" if len(slides) > 2 and len(slides[2]) > 52 else (slides[2] if len(slides) > 2 else "Why it matters for tech."))

    # Classify content type for visual diversity
    from src.media.visual_diversity import classify_content_type
    visual_type = classify_content_type(topic, " ".join(str(s) for s in slides[:3]))

    return {
        "content_type": content_type,
        "content_visual_type": visual_type,
        "reason": "Heuristic fallback from slide count and poster headlines.",
        "content_depth": depth,
        "audience_angle": "curiosity",
        "primary_claim": topic[:240],
        "hook_candidates": [cover.upper(), posters[1].upper() if len(posters) > 1 else cover.upper()],
        "hook_selected": cover.upper()[:95],
        "all_in_one_datapoint_1": d1[:60],
        "all_in_one_datapoint_2": d2[:60],
        "slide_plan": plan,
    }


def generate_story_brief(post: Dict[str, Any], cfg: AppConfig) -> Dict[str, Any]:
    """Call Gemini text model; on failure return fallback_story_brief."""
    api = (getattr(cfg, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY") or "").strip()
    if not api:
        log_stage(_LOG, "story_brief_fallback", "no_api_key")
        return fallback_story_brief(post)

    topic = str(post.get("topic") or "")
    slides = post.get("slides") or []
    sources = post.get("sources") or []
    src_lines = "\n".join(f"- {s.get('title','')}: {s.get('url','')}" for s in sources[:8])

    user = f"""Topic title: {topic}

Body slides (may be long):
{json.dumps(slides, ensure_ascii=False)[:12000]}

Sources:
{src_lines}

Produce the JSON brief. Enforce slide_plan length <= {_MAX_SLIDES}."""

    client = genai.Client(api_key=api)
    models = gemini_model_candidates(getattr(cfg, "gemini_model", None))
    persona = load_persona()
    combined = f"{_story_system_prompt(persona)}\n\n{user}"
    last_err: Optional[BaseException] = None
    text_out = ""
    for mid in models:
        try:
            resp = client.models.generate_content(
                model=mid,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=combined)])],
                config=types.GenerateContentConfig(
                    temperature=0.35,
                    response_mime_type="application/json",
                ),
            )
            cand = getattr(resp, "text", None) or ""
            if cand:
                text_out = cand
                break
            # fallback: stitch parts
            for c in getattr(resp, "candidates", None) or []:
                parts = getattr(getattr(c, "content", None), "parts", None) or []
                for p in parts:
                    t = getattr(p, "text", None)
                    if t:
                        text_out = t
                        break
        except Exception as e:  # noqa: BLE001
            last_err = e
            if is_gemini_model_unavailable_error(e):
                _LOG.warning("story_brief model retry %s %s", mid, e)
                continue
            _LOG.exception("story_brief fatal %s", mid)
            break

    parsed = _extract_json_object(text_out) if text_out else None
    if not isinstance(parsed, dict) or "slide_plan" not in parsed:
        log_stage(_LOG, "story_brief_fallback", "parse_or_empty", extra={"err": str(last_err)[:200]})
        return fallback_story_brief(post)

    plan = parsed.get("slide_plan")
    if not isinstance(plan, list) or not plan:
        return fallback_story_brief(post)

    plan = plan[:_MAX_SLIDES]
    parsed["slide_plan"] = plan
    ct = str(parsed.get("content_type") or "carousel").lower()
    if ct not in ("single", "carousel"):
        parsed["content_type"] = "carousel"
    if parsed["content_type"] == "single":
        parsed["slide_plan"] = plan[:1]

    log_stage(_LOG, "story_brief_ok", "ok", extra={"type": parsed.get("content_type"), "slides": len(parsed["slide_plan"])})
    return parsed


def ensure_story_brief(post: Dict[str, Any], cfg: AppConfig) -> Dict[str, Any]:
    if not story_strategist_enabled():
        return fallback_story_brief(post)
    return generate_story_brief(post, cfg)
