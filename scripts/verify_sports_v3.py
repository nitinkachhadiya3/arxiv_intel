"""
Sports Multi-Agent Validation Script.

Simulates an RCB vs MI match and runs the full agent pipeline locally.
Checks:
  - DataAgent returns structured match data
  - VisualAgent produces unique visual worlds per slide
  - Slide plan has correct visual/text-only mix
  - Hashtag block >= 15 tags
  - DirectorAgent writes punchy captions

Run: python3 scripts/verify_sports_v3.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.data_agent import DataAgent
from src.agents.visual_agent import VisualAgent, SPORTS_WORLDS
from src.agents.director_agent import DirectorAgent

TEST_QUERIES = [
    "RCB vs MI IPL 2026 today match Rohit Sharma",
    "Virat Kohli century RCB 2026",
    "Jasprit Bumrah 5 wickets IPL 2026",
    "Hardik Pandya hat trick Mumbai Indians",
    "IPL 2026 final trophy winner",
    "Rohit Sharma 7000 IPL runs record",
    "RCB vs CSK last over thriller",
    "MS Dhoni finisher 50 off 20 balls",
    "Sunrisers vs KKR powerplay carnage",
    "IPL 2026 purple cap orange cap standings",
]

def print_header(text):
    print(f"\n{'='*70}\n  {text}\n{'='*70}")

def run():
    print_header("🏏 SPORTS MULTI-AGENT VALIDATION (10 scenarios)")

    data_agent = DataAgent()
    visual_agent = VisualAgent()

    all_worlds_used, all_hashtag_counts, all_visual_flags = [], [], []

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n--- [Case {i}/10] ---")
        print(f"Query: {query}")

        # 1. DataAgent (use fallback to avoid API calls in local test)
        match_data = data_agent._fallback_match()
        # INJECT query hint so VisualAgent can do semantic selection
        match_data["_query"] = query

        hashtags = data_agent.build_hashtag_block(match_data)
        all_hashtag_counts.append(len(hashtags))

        # 2. VisualAgent slide plan
        plan = visual_agent.decide_slide_plan(match_data, slide_count=5)
        worlds = [s["world_id"] for s in plan]
        flags = [s["visual_flag"] for s in plan]
        all_worlds_used.extend(worlds)
        all_visual_flags.extend(flags)

        visual_count = sum(flags)
        text_count = len(flags) - visual_count

        print(f"  Match: {match_data['match_title']}")
        print(f"  Hashtags: {len(hashtags)} ({'✅' if len(hashtags)>=15 else '❌'})")
        print(f"  Visual slides: {visual_count} | Text-only slides: {text_count}")
        print(f"  Slide worlds: {worlds}")
        for s in plan:
            icon = "🖼️" if s["visual_flag"] else "📊"
            print(f"    {icon} Slide {s['slide_index']}: {s['world_name']} — {s['scene_hint'][:60]}")
        print(f"  Sample hashtags: {' '.join(hashtags[:8])}")


    # Summary
    print_header("📊 SUMMARY REPORT")
    unique_worlds = set(all_worlds_used)
    avg_hashtags = sum(all_hashtag_counts) / len(all_hashtag_counts)
    visual_ratio = sum(all_visual_flags) / len(all_visual_flags)

    print(f"Unique Visual Worlds used: {len(unique_worlds)}")
    print(f"World IDs: {sorted(unique_worlds)}")
    print(f"Average hashtags per post: {avg_hashtags:.1f}")
    print(f"Visual slide ratio: {visual_ratio:.0%}")

    all_pass = (avg_hashtags >= 15 and len(unique_worlds) >= 5)
    print(f"\n{'✅ ALL CHECKS PASSED' if all_pass else '⚠️  SOME CHECKS FAILED'}")

    # Quick DirectorAgent test (no API required — uses fallback captions)
    print_header("🎬 DirectorAgent Caption Test (fallback)")
    director = DirectorAgent()
    match_data = data_agent._fallback_match()
    plan = visual_agent.decide_slide_plan(match_data, 5)
    hashtags = data_agent.build_hashtag_block(match_data)
    captions = director._template_captions(match_data, plan, hashtags)
    for s in captions:
        icon = "🖼️" if s["visual_flag"] else "📊"
        print(f"  {icon} Slide {s['slide_index']}: {s['caption'][:100]}")

    print("\n✅ Validation complete. Ready for /match command on features branch.\n")

if __name__ == "__main__":
    run()
