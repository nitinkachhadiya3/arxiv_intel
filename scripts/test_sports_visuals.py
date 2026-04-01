import os
import random
from src.media.visual_diversity import build_diverse_prompt

def test_sports():
    # Mocking a sports topic
    topic = "IPL 2026: PBKS vs GT Strategic Dominance"
    
    # We need to see if we can inject a 'sports' world. 
    # Current code doesn't have one, so it will pick a tech world like 'editorial_office' or 'abstract_material'.
    prompt = build_diverse_prompt(
        content_type="sports",
        topic=topic,
        slide_index=1,
        total_slides=5
    )
    print("--- Current Prompt (Likely Tech-Heavy) ---")
    print(prompt)

if __name__ == "__main__":
    test_sports()
