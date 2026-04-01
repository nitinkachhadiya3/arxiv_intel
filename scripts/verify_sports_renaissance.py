import os
import logging
from dotenv import load_dotenv
from PIL import Image
from src.media.gemini_carousel_images import _apply_persona_descriptions
from src.media.editorial_compositor import (
    compose_cinematic_news_slide,
    compose_sports_stats_slide
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_sports_renaissance():
    print("🏟️ [TEST] Verifying Sports Broadcast Style & Persona Accuracy...")
    
    # 1. Test Persona Interceptor (The Ponting Fix)
    topic = "IPL News: Ricky Ponting's Vision for PKBS"
    base_prompt = "A high-end cinematic sports photograph from a professional match."
    refined_prompt = _apply_persona_descriptions(topic, base_prompt)
    
    print("\nStep 1: Testing Persona Interceptor...")
    if "authoritative older Australian cricket coach" in refined_prompt:
        print("✅ SUCCESS: Ponting's description added to prompt!")
    else:
        print("❌ FAILURE: Persona not detected.")

    # 2. Test Stats Card Layout
    print("\nStep 2: Testing Stats Card Compositor...")
    # Mock resources
    w, h = 1080, 1350
    base_img = Image.new("RGB", (w, h), (10, 15, 25))
    
    try:
        composed = compose_sports_stats_slide(
            base_img,
            headline="PBKS IMPACT METRICS",
            detail_lines=["Strike Rate: 165.2", "Economy: 7.82", "Wickets: 14"],
            font_title_candidates=["Arial.ttf"], # Generic for local test
            font_body_candidates=["Arial.ttf"],
            highlight_rgb=(255, 215, 0),
            primary_rgb=(255, 255, 255),
            accent_rgb=(255, 50, 50),
            logo_path=None
        )
        # Check if output is Image
        if isinstance(composed, Image.Image):
            print("✅ SUCCESS: Sports Stats Card composed successfully!")
            # Save for manual review if user wants
            composed.save("/tmp/stats_card_test.png")
    except Exception as e:
        print(f"❌ ERROR in Compositor: {e}")

if __name__ == "__main__":
    test_sports_renaissance()
