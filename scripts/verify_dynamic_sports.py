import os
import logging
from dotenv import load_dotenv
from src.media.gemini_carousel_images import build_cinematic_background_prompt
from src.media.visual_diversity import classify_content_type

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_dynamic_sports():
    print("🏏 [TEST] Verifying Dynamic IPL Visual Identity...")
    
    topic = "IPL 2026: PBKS vs GT High-Stakes Duel"
    hint = "A powerful right-handed batsman in a yellow jersey crushing a six under bright floodlights"
    
    # 1. Test Category Classification
    print("\nStep 1: Testing Keyword Classification...")
    cvt = classify_content_type(topic)
    print(f"✅ Classified as: {cvt}")
    
    # 2. Test Prompt Generation (Forcing Dynamic Sports)
    print("\nStep 2: Testing Prompt Generation (Dynamic Strategy)...")
    prompt = build_cinematic_background_prompt(
        topic_title=topic,
        slide_role="hook",
        semantic_visual_hint=hint,
        slide_index=1,
        total_slides=5,
        content_visual_type="sports"
    )
    
    print("\n--- Generated Prompt ---")
    print(prompt)
    
    # Check for core markers
    if "PROFESSIONAL SPORTS PHOTOGRAPHY" in prompt and "crushing a six" in prompt:
        print("\n✅ SUCCESS: Found story-specific action in prompt!")
    else:
        print("\n❌ FAILURE: Prompt does not reflect dynamic LLM input.")

if __name__ == "__main__":
    test_dynamic_sports()
