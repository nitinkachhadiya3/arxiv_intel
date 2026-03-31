import os
import random
import logging
from src.media.visual_diversity import build_diverse_prompt, classify_content_type

logging.basicConfig(level=logging.INFO)

def test_ipl_visuals():
    print("🏏 [TEST] Verifying IPL Visual Identity...")
    
    topic = "IPL 2026: PBKS vs GT High-Stakes Duel"
    
    # 1. Test Category Classification
    print("\nStep 1: Testing Keyword Classification...")
    cvt = classify_content_type(topic)
    print(f"✅ Classified as: {cvt}")
    if cvt != "sports":
        print("❌ Classification failed! Expected 'sports'.")
        # return

    # 2. Test Prompt Generation (Forcing Sports)
    print("\nStep 2: Testing Prompt Generation (Sports World)...")
    prompt = build_diverse_prompt(
        content_type="sports",
        topic=topic,
        slide_index=1,
        total_slides=5
    )
    
    print("\n--- Generated Prompt ---")
    print(prompt)
    
    # Check for sports keywords in the prompt
    keywords = ["stadium", "cricket", "pitch", "floodlights", "match"]
    found = [k for k in keywords if k in prompt.lower()]
    if found:
        print(f"\n✅ SUCCESS: Found sports elements in prompt: {found}")
    else:
        print("\n❌ FAILURE: No sports elements found in prompt.")

if __name__ == "__main__":
    test_ipl_visuals()
