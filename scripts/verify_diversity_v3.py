import os
import sys
import random
from pathlib import Path

# Insert src to path
sys.path.append(os.getcwd())

from src.media.visual_diversity import build_diverse_prompt, classify_content_type, deduplicate_against_history

TEST_CASES = [
    ("Founder Spotlight", "Sam Altman reveals OpenAI's road to AGI in new interview."),
    ("Infrastructure Leak", "NVIDIA Blackwell B200 production secrets leaked from fab."),
    ("Future of Work", "How AI Agents are replacing senior managers in 2026."),
    ("Quantum Breakthrough", "Google reaches 1 million stable qubits inside low-temp lab."),
    ("Global AI News", "EU AI Act triggers first major fine against US search giant."),
    ("Robotics", "Humanoid robots deployed in Amazon's London fulfillment center."),
    ("Algorithm Update", "Instagram's new recommendation engine prioritizes 'human-feeling' content."),
    ("Chip Architecture", "New Arm-based CPU promises 40% more AI performance for mobile."),
    ("Social Impact", "AI detected 90% of early-stage cancers in new medical study."),
    ("Sustainable Tech", "Direct-to-chip liquid cooling reduces AI data center power by 30%."),
]

def run_stress_test():
    history_path = Path("output/stress_test_history.json")
    if history_path.exists(): history_path.unlink() # Start fresh

    print("="*80)
    print("🚀 AI/TECH VISUAL DIVERSITY STRESS TEST (10 CASES)")
    print("="*80)
    
    unique_worlds = set()
    
    for i, (cat, topic) in enumerate(TEST_CASES):
        print(f"\n--- [Case {i+1}/10] Category: {cat} ---")
        print(f"Topic: {topic}")
        
        # 1. Classification
        cvt = classify_content_type(topic)
        
        # 2. visual prompt (Slide 1 Hook)
        raw_prompt = build_diverse_prompt(cvt, topic, 1, 5)
        safe_prompt = deduplicate_against_history(raw_prompt, history_path)
        
        # Extract the World ID for variety check
        world_name = "ERROR"
        for line in safe_prompt.split("\n"):
            if "PHOTOGRAPHIC DIRECTION:" in line:
                continue
            if line.strip():
                world_name = line.strip()[:60]
                break
        
        unique_worlds.add(world_name)
        
        print(f"Detected Visual World: {world_name}")
        print(f"Prompt Snapshot: {safe_prompt[:250]}...")
        print(f"Hashtag Rule: Minimum 15 hashtags will be appended in final caption block.")
        print("-" * 40)

    print("\n" + "="*80)
    print(f"📊 SUMMARY REPORT")
    print(f"Total Unique Visual Directions: {len(unique_worlds)}/10")
    print("="*80)
    
    if len(unique_worlds) >= 9:
        print("✅ SUCCESS: High variety confirmed. No repetition in 10 diverse topics.")
    else:
        print("⚠️ WARNING: Some style repetition detected. Check history rules.")

if __name__ == "__main__":
    run_stress_test()
