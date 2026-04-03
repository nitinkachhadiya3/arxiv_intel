"""
Visual Diversity Engine v4: SEMANTIC-MAPPING + CINEMATIC-TECH.
Optimized for the 'dev' branch (AI/Tech vertical).
Uses keyword-based mapping to ensure visuals match the topic perfectly
(e.g., Founders get portraits, Chips get hardware detail).
"""

from __future__ import annotations

import json
import hashlib
import random
import time
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── BLACKLIST: motifs that make every post look the same ─────────────────

_BANNED_MOTIFS = (
    "COLOR GRADING & VIBRANCY:\n"
    "- Make the image highly vibrant, colorful, and beautifully saturated.\n"
    "- Avoid dull or purely dark monochrome unless heavily requested.\n"
    "The image must look like a high-end, colorful editorial feature for Wired or Bloomberg.\n"
)

# ── 24 distinct visual "worlds" with GPT-Style Cinematic Prompts ──────────

VISUAL_WORLDS: List[Dict[str, Any]] = [
    {
        "id": "strategic_visionary",
        "name": "Strategic Visionary Portrait",
        "prompt": (
            "Ultra-realistic professional editorial portrait of a technical CEO or founder. "
            "Focused, intense expression, detailed human skin textures, cinematic lighting. "
            "Modern glass and wood office background, soft natural bokeh. "
            "8k resolution, shot on Hasselblad H6D, 80mm lens, f/2.8, cinematic depth of field, "
            "color graded for a premium tech publication. High realism."
        ),
        "mood": "authoritative, human, visionary",
    },
    {
        "id": "macro_innovation",
        "name": "Semiconductor Precision",
        "prompt": (
            "Highly detailed macro photography of a futuristic semiconductor chip or circuit. "
            "Close-up of silicon architecture, golden circuit lines glowing with energy, "
            "prismatic light reflections on glass and metal surfaces. 8k realism, "
            "sharp focus on the micro-details, low-angle perspective. "
            "Professional product photography, cinematic lighting and depth of field."
        ),
        "mood": "precise, high-value, electronic",
    },
    {
        "id": "robotic_automation",
        "name": "Advanced Robotics",
        "prompt": (
            "Cinematic photograph of advanced humanoid robots in a futuristic factory or warehouse. "
            "Robotic arms with precise articulation, white and carbon-fiber casing, "
            "interacting with real-world objects or human technicians. "
            "8k resolution, dramatic industrial side-lighting, realistic shadows and reflections, "
            "shallow depth of field. High-tech automation aesthetic."
        ),
        "mood": "automated, precise, mechanical",
    },
    {
        "id": "quantum_lab",
        "name": "Quantum Computing Lab",
        "prompt": (
            "Futuristic quantum computing laboratory. Large glowing cryogenic dilution refrigerator "
            "with intricate copper and gold wiring patterns. Scientists in professional cleanroom suits "
            "monitoring complex digital interfaces. 8k realism, blue and amber neon highlights, "
            "atmospheric fog, cinematic reflections on polished floors. Professional research quality."
        ),
        "mood": "scientific, advanced, nocturnal",
    },
    {
        "id": "global_node",
        "name": "Digital Architecture",
        "prompt": (
            "Stunning architectural photography of a modern tech parliament or headquarters building. "
            "Dramatic geometry, glass and steel surfaces reflecting a storm sky or sunset glow. "
            "Subtle digital interface overlays representing connectivity flux. 8k realism, "
            "professional tilt-shift lens look, perfect vertical lines, cinematic color grade."
        ),
        "mood": "grand, geometric, connected",
    },
    {
        "id": "data_fluids",
        "name": "Abstract Data Dynamics",
        "prompt": (
            "Artistic abstract photograph of flowing liquid-like data streams or particles. "
            "Iridescent silver and deep neon blue swirling patterns, crystalline sharp textures. "
            "8k resolution, cinematic lighting effects, ray-tracing style reflections. "
            "Abstract but photographic, NOT a 3D render. Premium digital art aesthetic."
        ),
        "mood": "fluid, intelligent, abstract",
    },
    {
        "id": "cyber_botany",
        "name": "Sustainable Biotech",
        "prompt": (
            "Ultra-realistic close-up of a living green leaf with micro-circuits "
            "beautifully etched into its surface. Realistic sunlight filtering through, "
            "macro texture detail of both plant and metal. 8k realism, nature meets tech "
            "in a grounded, realistic environmental portrait. High-end eco-innovation style."
        ),
        "mood": "natural, hybrid, sustainable",
    },
    {
        "id": "strategic_blueprint",
        "name": "Architectural Design",
        "prompt": (
            "Top-down cinematic flat-lay of a complex technical blueprint or strategic map. "
            "High-end drafting tools, single brass compass, shadows from a desk lamp. "
            "Realistic paper texture, precise penciled lines, 8k resolution. "
            "Tactile, old-school engineering aesthetic meets futuristic planning."
        ),
        "mood": "planning, precise, classic",
    },
    {
        "id": "dev_noire",
        "name": "Nocturnal Coding",
        "prompt": (
            "Moody close-up of a high-end mechanical keyboard and smartphone in a dark room. "
            "A single purple or green glow from the screen lighting the interface. "
            "Focus on the tactile keys, motion blur of typing. 8k realism, "
            "cinematic low-light photography, shallow depth of field. High-tech noir mood."
        ),
        "mood": "focused, nocturnal, tactical",
    },
    {
        "id": "industrial_shift",
        "name": "Industrial Night Shift",
        "prompt": (
            "Cinematic wide-shot of a massive data center or automated factory at night. "
            "Rows of servers with glowing blue status lights, steam rising from cooling vents, "
            "lone engineer silhouette in the distance. 8k realism, industrial power aesthetic, "
            "dynamic lighting, professional photography style."
        ),
        "mood": "powerful, nocturnal, massive",
    },
    {
        "id": "digital_ink",
        "name": "Minimalist Form",
        "prompt": (
            "Minimalist abstract of black and white fluid patterns resembling digital ink. "
            "High-contrast, razor-sharp edges, elegant organic curves. 8k resolution, "
            "premium brand identity aesthetic, professional studio lighting. "
            "Represents the pure form of intelligence. Stark, elegant, refined."
        ),
        "mood": "minimalist, elegant, stark",
    },
    {
        "id": "expert_hands",
        "name": "Precision Craft",
        "prompt": (
            "Highly detailed close-up of human hands assembling a delicate AI-chip component. "
            "Microscopic tweezers, golden wiring, magnifying glass lens flare. "
            "8k realism, warm skin tones against cold metallic surfaces, "
            "professional macro photography style, shallow depth of field. Precise human skill."
        ),
        "mood": "precise, human, skilled",
    },
    {
        "id": "human_insight_portrait",
        "name": "Human Intelligence",
        "prompt": (
            "Ultra-realistic candid portrait of an expert researcher in deep thought. "
            "Natural window light, detailed skin textures including fine lines and pores. "
            "Blurred library or computer screens in background. 8k realism, "
            "emotional and intellectual depth, professional environmental portraiture style."
        ),
        "mood": "wise, contemplative, human",
    },
    {
        "id": "future_interior",
        "name": "Parametric Design",
        "prompt": (
            "Stunning architectural interior of a tech headquarters atrium. "
            "Curved white parametric walls, organic Zaha Hadid style architecture. "
            "Professional wide-angle photography, clean natural lighting from skylights. "
            "8k realism, sense of space and forward-thinking design. Minimalist and grand."
        ),
        "mood": "grand, futuristic, architectural",
    },
    {
        "id": "micro_optics",
        "name": "Optical Vision",
        "prompt": (
            "Extreme macro photograph of high-end camera optics or telescope mirrors. "
            "Circular reflections of a studio monitor, iridescent lens coatings, "
            "perfectly polished surfaces. 8k realism, visualizing the 'Eye of AI', "
            "razor-sharp focus, professional lens flare. Optical perfection."
        ),
        "mood": "observant, precise, optical",
    },
    {
        "id": "data_mountain",
        "name": "Geometric Landscape",
        "prompt": (
            "Aerial drone photography of an arid landscape with geometric irrigation "
            "or solar patterns cut into the earth. Resembles a massive CPU layout or QR code. "
            "8k resolution, warm sun-drenched palette, vast scale, highly detailed earth textures. "
            "Cinematic landscape quality, professional color grading."
        ),
        "mood": "vast, geometric, surreal",
    },
    {
        "id": "liquid_gold",
        "name": "Forging Technology",
        "prompt": (
            "Cinematic macro of molten copper or gold being poured in a high-tech foundry. "
            "Glowing heat, fluid mercury-like motion, sparks flying, deep shadows. "
            "8k resolution, high dynamic range, industrial power and heat aesthetic. "
            "Visualizing the manufacturing of core technology."
        ),
        "mood": "hot, fluid, powerful",
    },
    {
        "id": "clean_white_abstract",
        "name": "Mental Canvas",
        "prompt": (
            "High-contrast abstract of folded white photographic paper. "
            "Dramatic sharp shadows creating geometric triangles and planes. "
            "8k resolution, clean minimalist aesthetic, professional studio lighting. "
            "Represents the blank canvas of innovation. Sterile, elegant, structured."
        ),
        "mood": "clean, minimal, structured",
    },
    {
        "id": "satellite_node",
        "name": "Global Connectivity",
        "prompt": (
            "Ultra-high-res digital satellite view of a metropolitan grid at night. "
            "Glowing golden arteries of data flow (traffic), dark blocks of high-rises. "
            "8k resolution, cinematic atmosphere, visualizing the planet as a circuit board. "
            "Professional map-style photography, high contrast."
        ),
        "mood": "global, macro, connected",
    },
    {
        "id": "team_war_room",
        "name": "Collaboration Hub",
        "prompt": (
            "Dynamic environmental portrait of a diverse technical team in a strategy war room. "
            "Focused expressions, team collaborating around a glowing conference table, "
            "blurred code and analytics on screens in background. 8k realism, "
            "handheld camera feel (2470 GM II look), cinematic color grade, authentic human interaction."
        ),
        "mood": "collaborative, intense, human",
    },
    {
        "id": "quantum_space",
        "name": "Latent Space",
        "prompt": (
            "Artistic abstract of multi-dimensional light space. Golden dust particles "
            "floating in deep velvet blackness, soft light leaks, ethereal atmosphere. "
            "8k resolution, high dynamic range, cinematic dream-like quality. "
            "Visualizing the latent space of a neural network. Mysterious and deep."
        ),
        "mood": "mysterious, ethereal, deep",
    },
    {
        "id": "future_urban_shuttle",
        "name": "Autonomous Mobility",
        "prompt": (
            "Cinematic street photography of an autonomous vehicle or drone passing "
            "through a modern city district. Motion blur of city lights, "
            "sleek reflective surfaces of the vehicle. 8k realism, Leica 35mm look, "
            "gritty urban atmosphere, professional reportage style."
        ),
        "mood": "fast-paced, connected, urban",
    },
    {
        "id": "macro_eye",
        "name": "Neural Gaze",
        "prompt": (
            "Macro photography of a human iris with subtle digital data reflections. "
            "Extreme detail of the pupil and muscle fibers of the eye. "
            "8k resolution, professional macro lens (90mm G OSS look), sharp focus, "
            "cinematic lighting. High realism, capturing the moment of insight."
        ),
        "mood": "observant, intelligent, human",
    },
    {
        "id": "glass_refraction",
        "name": "Optical Prism",
        "prompt": (
            "Macro photography of light passing through dense textured glass prisms. "
            "Sharp light leaks, prismatic rainbow refractions, soft bokeh, deep golden hues. "
            "8k resolution, atmospheric professional studio lighting, high-end editorial quality. "
            "Textural, warm, and artistic."
        ),
        "mood": "warm, prismatic, artistic",
    },
]

# ── SEMANTIC KEYWORD MAPPING ─────────────────────────────────────────────

SEMANTIC_MAP: Dict[str, str] = {
    # Founders / People
    r"\b(sam altman|ceo|founder|elon musk|founder|leader|visionary|expert|team|researcher|person|people)\b": "strategic_visionary",
    # Chips / Hardware
    r"\b(chip|nvidia|blackwell|b200|semiconductor|hardware|processor|cpu|gpu|computing|wafer|fab)\b": "macro_innovation",
    # Robotics
    r"\b(robot|humanoid|robotics|automation|factory|warehouse|amazon|picking|mechanical)\b": "robotic_automation",
    # Science / Quantum
    r"\b(quantum|lab|laboratory|qubit|stable|low-temp|cryo|science|research)\b": "quantum_lab",
    # Global / Regulation
    r"\b(regulation|eu|ai act|law|fine|parliament|government|policy|legal)\b": "global_node",
    # Data / Fluids
    r"\b(algorithm|data|flow|swirl|fluid|model|training|intelligence)\b": "data_fluids",
    # Sustainable
    r"\b(sustainable|liquid|cooling|energy|green|eco|environment)\b": "cyber_botany",
    # Strategy
    r"\b(strategic|plan|roadmap|blueprint|secret|leak|drawings)\b": "strategic_blueprint",
}

# ── Per-slide variation within a world ───────────────────────────────────

_SLIDE_VARIATIONS = {
    1: {  # HOOK — most dramatic
        "instruction": (
            "HOOK SLIDE: Ultra-striking, hyper-dramatic composition. Visually stunning, must instantly grab attention and dominate the viewer's screen."
        ),
        "framing": ["vast cinematic wide shot", "extreme low angle looking up", "surreal symmetrical composition"],
    },
    2: {  # CONTEXT — human scale
        "instruction": (
            "CONTEXT SLIDE: Realistic human-scale perspective, medium composition."
        ),
        "framing": ["medium eye-level", "over-the-shoulder", "environmental portrait"],
    },
    3: {  # DETAIL — macro
        "instruction": (
            "DETAIL SLIDE: High-detail macro shot, focused on a specific component or texture."
        ),
        "framing": ["macro close-up", "extreme detail", "top-down flat-lay"],
    },
    4: {  # CTA — minimal
        "instruction": (
            "CTA SLIDE: Minimalist, clean composition for clear text overlay."
        ),
        "framing": ["clean centered", "soft bokeh landscape", "minimal high-contrast"],
    },
}

def _get_slide_variation(slide_index: int, total_slides: int, rng: random.Random) -> Dict:
    """Get slide-specific variation rules."""
    if slide_index == 1: return _SLIDE_VARIATIONS[1]
    elif slide_index == total_slides: return _SLIDE_VARIATIONS[4]
    elif slide_index == 2: return _SLIDE_VARIATIONS[2]
    else: return _SLIDE_VARIATIONS[3]

def _pick_semantic_world(topic: str, visual_hint: str, slide_index: int, rng: random.Random) -> Dict[str, Any]:
    """Slide-based semantic world selection preferring visual_hint over global topic."""
    
    # 1. Deep Semantic Matching: Prioritize the specific visual_hint for this slide
    hint_lower = visual_hint.lower()
    for pattern, world_id in SEMANTIC_MAP.items():
        if hint_lower and re.search(pattern, hint_lower):
            world = next((w for w in VISUAL_WORLDS if w["id"] == world_id), None)
            if world: return world
            
    # 2. Topic Matching: Only tightly couple Slide 1 to the raw topic, let others drift if unset
    if slide_index == 1:
        t_lower = topic.lower()
        for pattern, world_id in SEMANTIC_MAP.items():
            if re.search(pattern, t_lower):
                world = next((w for w in VISUAL_WORLDS if w["id"] == world_id), None)
                if world: return world
    
    # 3. True Randomness: Complete decoupling array for extreme carousel diversity
    return rng.choice(VISUAL_WORLDS)

def build_diverse_prompt(
    content_type: str,
    topic: str,
    slide_index: int,
    total_slides: int,
    visual_hint: str = "",
    rng: Optional[random.Random] = None,
) -> str:
    """Build a photorealistic, semantic, cinematic prompt."""
    if rng is None:
        # Time-salt to completely blast caching across identical topic runs
        rng = random.Random(int(time.time() * 1000) + slide_index * 999)

    world = _pick_semantic_world(topic, visual_hint, slide_index, rng)
    slide_var = _get_slide_variation(slide_index, total_slides, rng)
    framing = rng.choice(slide_var["framing"])

    # Gently clean up hint instead of brutally dropping it
    hint_block = ""
    if visual_hint:
        clean_hint = re.sub(r"(?i)\b(holographic|neon|cyber|matrix|wireframe)\b", "cinematic", visual_hint)
        hint_block = f"\nPRIMARY VISUAL DIRECTIVE (FROM USER/REFERENCE): {clean_hint}\nThe above directive is the most important constraint. Generate the image EXACTLY as described above, overriding the Visual World if they conflict. Use vibrant colors.\n"

    unique_hash = hex(rng.getrandbits(32))[2:]
    
    prompt = f"""[UNIQUE SCENE SEED: {unique_hash} | SLIDE {slide_index}/{total_slides}]
Specific Scene Composition for this frame: {framing}
Slide objective: {slide_var['instruction']}{hint_block}

Topic context: {topic}

PHOTOGRAPHIC DIRECTION:
{world['prompt']}

Visual World Identity: {world['name']} ({world['mood']})

{_BANNED_MOTIFS}
COMPOSITION RULE: Keep main action in the upper 65% of frame. The bottom 35% must be clear for text.

OUTPUT: Ultra-realistic, 8k cinematic photograph. NOT AI-looking. NO generic stock motifs.
""".strip()

    return prompt

def deduplicate_against_history(
    prompt: str,
    history_path: Path,
    max_history: int = 15,
    rng: Optional[random.Random] = None,
) -> str:
    """Style history deduplication."""
    if rng is None: rng = random.Random()
    history = []
    if history_path.exists():
        try:
            data = json.loads(history_path.read_text(encoding="utf-8"))
            if isinstance(data, list): history = [str(h) for h in data[-max_history:]]
        except: pass

    current_world_ids = [w["id"] for w in VISUAL_WORLDS if w["prompt"][:60] in prompt]
    if current_world_ids:
        current_id = current_world_ids[0]
        recent_ids = []
        for h in history[-8:]:
            for w in VISUAL_WORLDS:
                if w["prompt"][:60] in h:
                    recent_ids.append(w["id"])
                    break
        # Force a unique style ONLY for non-semantic fallback posts
        # (Semantic posts about specific topics SHOULD override history if relevant).
        # We handle this by softening the replacement rule for semantic matches.

    history.append(prompt)
    history = history[-max_history:]
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return prompt

def classify_content_type(topic: str, body: str = "") -> str:
    """Keyword-based classification for the 'dev' AI/Tech branch."""
    combined = (topic + " " + body).lower()
    if re.search(r"\b(ceo|founder|cto|expert|team|founder)\b", combined): return "founder"
    if re.search(r"\b(chip|server|data center|compute|gpu|infrastructure)\b", combined): return "infrastructure"
    return "news"
