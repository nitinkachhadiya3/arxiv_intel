"""
End-to-end sports pipeline test.

Traces the EXACT path from DirectorAgent → CarouselImageGenerator → Gemini Image API
to verify that sports visual prompts (not AI/Tech prompts) reach the image generation stage.

Run: .venv/bin/python3 scripts/test_sports_e2e.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
load_dotenv(root / ".env", override=True)
key = os.getenv("GEMINI_API_KEY", "").strip()
if key:
    os.environ["GOOGLE_API_KEY"] = key

from src.agents.director_agent import DirectorAgent
from src.media.image_generator import CarouselImageGenerator
import uuid, tempfile

def test_prompt_routing():
    """Verify the prompts that actually reach Gemini are SPORTS prompts, not tech."""
    print("="*70)
    print("  🏏 SPORTS E2E PROMPT ROUTING TEST")
    print("="*70)

    # 1. Generate slides via Director
    director = DirectorAgent()
    drafts = director.generate_sports_post(query="RCB vs MI IPL 2026", slide_count=5, draft_count=1)
    draft = drafts[0]
    slides = draft["slides"]
    match_data = draft["match_data"]

    print(f"\n✅ Director generated {len(slides)} slides")
    print(f"   Match: {match_data.get('match_title', '?')}")

    # 2. Build the story_post exactly like sports_core.py does
    visual_prompts = [s.get("image_prompt", "") for s in slides]
    visual_flags = [s.get("visual_flag", True) for s in slides]
    slide_types = ["IMAGE" if s.get("visual_flag", True) else "STATS" for s in slides]
    slide_texts = [s.get("caption", "") for s in slides]
    match_title = match_data.get("match_title", "IPL 2026")

    story_post = {
        **match_data,
        "content_visual_type": "sports",
        "content_source": "ipl_grounding",
        "visual_flags": visual_flags,
        "visual_prompts": visual_prompts,
        "slide_types": slide_types,
        "slides": slide_texts,
        "poster_headlines": slide_texts,
        "topic": match_title,
        "cover_headline": slide_texts[0][:80] if slide_texts else match_title,
    }

    print(f"\n✅ story_post built:")
    print(f"   content_visual_type = {story_post.get('content_visual_type')}")
    print(f"   content_source = {story_post.get('content_source')}")
    print(f"   slide_types = {slide_types}")

    # 3. Check visual prompts contain cricket keywords (not tech)
    print(f"\n📸 Visual Prompts (checking for cricket content):")
    cricket_keywords = ["cricket", "stadium", "batsman", "bowler", "ipl", "bat", "wicket",
                        "crowd", "floodlight", "jersey", "pitch", "sports", "yorker",
                        "six", "match", "over", "innings"]
    tech_keywords = ["laptop", "circuit", "processor", "neural", "holographic", "building",
                     "server", "cloud computing", "data center", "silicon"]

    for i, vp in enumerate(visual_prompts):
        is_visual = visual_flags[i]
        icon = "🖼️" if is_visual else "📊"
        print(f"\n  {icon} Slide {i+1} ({slide_types[i]}):")

        if not vp:
            print(f"     [No image prompt — text-only slide] ✅")
            continue

        # Check for cricket keywords
        vp_lower = vp.lower()
        found_cricket = [kw for kw in cricket_keywords if kw in vp_lower]
        found_tech = [kw for kw in tech_keywords if kw in vp_lower]

        print(f"     Prompt preview: {vp[:120]}...")
        print(f"     Cricket keywords found: {found_cricket[:5]}")
        if found_tech:
            print(f"     ⚠️  TECH KEYWORDS DETECTED: {found_tech}")
        else:
            print(f"     ✅ No tech contamination")

    # 4. Verify story_brief preserves sports type
    from src.content.story_brief import ensure_story_brief
    from src.utils.config import get_config
    cfg = get_config()

    base_post = {
        "topic": match_title,
        "slides": slide_texts,
        "poster_headlines": slide_texts,
        "visual_prompts": visual_prompts,
        "cover_headline": slide_texts[0][:80] if slide_texts else match_title,
        "sources": [],
        "content_visual_type": "sports",
        "content_source": "ipl_grounding",
    }
    brief = ensure_story_brief(base_post, cfg)

    print(f"\n📋 Story Brief Check:")
    print(f"   content_visual_type = {brief.get('content_visual_type')}")
    print(f"   content_source = {brief.get('content_source', 'N/A')}")
    cvt = brief.get("content_visual_type", "")
    if cvt == "sports":
        print(f"   ✅ Sports type preserved through story brief!")
    else:
        print(f"   ❌ FAIL: Sports type lost — got '{cvt}' instead!")

    # 5. Actually render 1 slide to disk (real Gemini API call)
    print(f"\n🎨 Rendering slide 1 (real Gemini image generation)...")
    generator = CarouselImageGenerator()
    slug = f"sports_test_{uuid.uuid4().hex[:6]}"
    out_dir = Path(root / "output" / "sports_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        media_paths = generator.render_topic_slides(
            topic_slug=slug,
            slide_texts=slide_texts[:1],  # Only render slide 1 for speed
            out_dir=out_dir,
            topic_title=match_title,
            cover_headline=slide_texts[0][:80] if slide_texts else match_title,
            visual_prompts=visual_prompts[:1],
            story_post=story_post,
            slide_types=slide_types[:1],
        )
        if media_paths:
            print(f"   ✅ Generated: {media_paths[0]}")
            print(f"   File size: {media_paths[0].stat().st_size / 1024:.0f} KB")

            # Check the saved prompt
            meta_dir = out_dir / "_meta"
            prompt_file = meta_dir / "slide_01_prompt.txt"
            if prompt_file.exists():
                prompt_text = prompt_file.read_text()
                print(f"\n   📝 ACTUAL PROMPT SENT TO GEMINI (first 300 chars):")
                print(f"   {prompt_text[:300]}")

                # Final check: does the prompt contain sports content?
                if any(kw in prompt_text.lower() for kw in ["cricket", "stadium", "sports", "ipl", "batsman"]):
                    print(f"\n   ✅ CONFIRMED: Sports prompt reached Gemini!")
                else:
                    print(f"\n   ❌ FAIL: Prompt does NOT contain cricket/sports keywords!")
        else:
            print(f"   ❌ No images generated")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print(f"\n{'='*70}")
    print(f"  🏏 TEST COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_prompt_routing()
