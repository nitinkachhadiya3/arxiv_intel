import os
import yaml
from pathlib import Path
from src.utils.logger import get_logger

_LOG = get_logger("content.persona_loader")

import json

def load_persona(persona_id: str = "") -> dict:
    """Load persona config from config/personas directory. Fallback to technology if not found."""
    root = Path(__file__).resolve().parent.parent.parent
    history_path = root / "data" / "processed" / "published_posts.jsonl"

    total_posts = 0
    recent_topics = []
    if history_path.is_file():
        try:
            lines = history_path.read_text(encoding="utf-8").splitlines()
            valid_lines = [l for l in lines if l.strip()]
            total_posts = len(valid_lines)
            for line in reversed(valid_lines[-10:]):
                try:
                    row = json.loads(line)
                    t = str(row.get("topic") or "").strip()
                    if t and t not in recent_topics:
                        recent_topics.append(t)
                except Exception:
                    pass
        except Exception:
            pass

    if not persona_id:
        env_cat = (os.getenv("CONTENT_CATEGORY") or "").strip()
        if env_cat:
            persona_id = env_cat
        else:
            # Locked to technology as per user request
            persona_id = "technology"

    persona_dir = root / "config" / "personas"
    target_path = persona_dir / f"{persona_id}.yaml"

    if not target_path.is_file():
        _LOG.warning("Persona '%s' not found at %s. Falling back to 'technology'", persona_id, target_path)
        target_path = persona_dir / "technology.yaml"

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            persona = data if data else _default_tech_persona()
    except Exception as e:
        _LOG.error("Failed to parse persona YAML %s: %s", target_path, e)
        persona = _default_tech_persona()

    if recent_topics:
        anti_rep = (
            "\nCRITICAL ANTI-REPETITION RULE: The following topics have been published recently. "
            "You MUST output tangibly different visual angles, structures, and content themes:\n"
            + "\n".join(f"- {t}" for t in recent_topics)
        )
        if "story_strategist" in persona:
            current_role = persona["story_strategist"].get("system_role", "")
            persona["story_strategist"]["system_role"] = current_role + "\n" + anti_rep
        
        if "image_generation" in persona:
            guardrails = persona["image_generation"].get("guardrails", [])
            topics_snippet = ", ".join(recent_topics[:4])
            guardrails.insert(0, f"Ensure the composition is completely distinct from our recent stories: {topics_snippet}")
            persona["image_generation"]["guardrails"] = guardrails

    return persona

def _default_tech_persona() -> dict:
    return {
        "id": "technology",
        "name": "Tech News Standard",
        "category": "technology",
        "story_strategist": {
            "system_role": "You are the editorial strategist for a premium technology-news Instagram brand.",
            "primary_focus": "technical innovation, product updates, enterprise technology"
        },
        "image_generation": {
            "visual_style": "Ultra-detailed cinematic 3D or photoreal still, dramatic lighting, high contrast, sharp focus.\nNews-worthy energy without sensationalist hoaxes. Professional photography / blockbuster color grade; depth and atmosphere.",
            "guardrails": [
                "NO text, letters, numbers, logos, watermarks, captions, UI, or HUD in the image",
                "NO photorealistic identifiable celebrities or politicians",
                "NO depictions of real-world disasters, terror, gore, or 'company HQ on fire / explosion' scenes",
                "If tension is needed, use symbolic tech imagery (abstract energy, generic silhouettes, maps, networks) not hoax photojournalism",
                "Do not invent specific breaking-news events; illustrate the industry theme visually"
            ]
        }
    }
