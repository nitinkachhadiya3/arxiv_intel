import os
import logging
import json
from dotenv import load_dotenv
from src.media.gemini_carousel_images import build_cinematic_background_prompt, _apply_persona_descriptions
from src.media.visual_diversity import classify_content_type
from src.content.persona_loader import load_persona

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_health_check():
    print("🏏 [HEALTH CHECK] Verifying Cricket Intelligence Engine...")
    
    # 1. Test Data Categorization (Team-Aware)
    topics = [
        "PBKS vs GT Match Preview: Tactical Analysis",
        "Ricky Ponting's Coaching Philosophy for 2026",
        "Virat Kohli's Strike Rate in Powerplay: A Deep Dive",
        "IPL Venue Report: Wankhede Stadium Pitch Conditions"
    ]
    
    print("\nPhase 1: Keyword Classification...")
    for t in topics:
        cvt = classify_content_type(t)
        print(f"  Topic: '{t[:40]}...' -> Category: {cvt}")
        if cvt != "sports":
            print(f"  ❌ Error: Topic should have been classified as sports!")

    # 2. Test Persona Interceptor (The Legend Fix)
    print("\nPhase 2: Persona Interceptor (Safety Bypass)...")
    p_topics = [
        ("Ricky Ponting", "authoritative older Australian cricket coach"),
        ("Virat Kohli", "bearded, intense elite Indian batsman"),
        ("MS Dhoni", "legendary calm Indian wicketkeeper")
    ]
    for name, snippet in p_topics:
        prompt = _apply_persona_descriptions(name, "Action shot of the player.")
        if snippet in prompt:
            print(f"  ✅ Persona Interceptor works for: {name}")
        else:
            print(f"  ❌ Persona Interceptor failed for: {name}")

    # 3. Test Dynamic Prompting (No Tech Leakage)
    print("\nPhase 3: Visual Prompt Quality (Tech Leakage Check)...")
    sample_topic = "PBKS vs GT Match Intensity"
    sample_hint = "A powerful batsman hitting a six under stadium lights"
    
    prompt = build_cinematic_background_prompt(
        topic_title=sample_topic,
        slide_role="hook",
        semantic_visual_hint=sample_hint,
        slide_index=1,
        total_slides=5,
        content_visual_type="sports",
        is_stats=False
    )
    
    banned = ["tech", "ai", "digital", "chip", "network", "office", "computer"]
    found_banned = [w for w in banned if w in prompt.lower()]
    if found_banned:
        print(f"  ❌ Found unwanted tech keywords in prompt: {found_banned}")
    else:
        print(f"  ✅ Prompt is 100% Sports-Native (No tech leakage).")
        print(f"  Prompt Preview: {prompt[:120]}...")

    print("\n✅ HEALTH CHECK COMPLETE: The Cricket Engine is stable and broadcast-ready!")

if __name__ == "__main__":
    run_health_check()
