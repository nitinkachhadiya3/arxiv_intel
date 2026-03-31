import os
import sys
import uuid
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env")
sys.path.append(os.getcwd())

from src.bot.core import generate_custom_previews

def test_custom_carousel_remix():
    print("Testing 'Custom Carousel Remix' (Slide 1: Hero, Slide 2+: Content)...")
    
    # Using a single reference image for professional tech lifestyle
    ref_urls = ["https://images.unsplash.com/photo-1560250097-0b93528c311a?w=800&q=80"]
    description = "Create a carousel about the future of AI Agent architectures. Slide 1 should remix the sleek professional vibe of the reference."
    
    try:
        # Generate 1 draft (which should now have 3-5 slides)
        drafts = generate_custom_previews(description, ref_urls)
        
        if not drafts:
            print("❌ FAILED: No drafts generated.")
            return

        draft = drafts[0]
        media_count = len(draft.get("media_urls", []))
        print(f"Successfully generated draft with {media_count} slides.")
        print(f"Main Caption: {draft['caption']}")
        
        if media_count >= 3:
            print(f"✅ SUCCESS: Generated a multi-slide carousel ({media_count} slides).")
        else:
            print(f"⚠️ WARNING: Carousel only has {media_count} slides, expected 3+.")
            
        for i, url in enumerate(draft["media_urls"]):
            print(f"  Slide {i+1} URL: {url}")
            
    except Exception as e:
        print(f"❌ FAILED: Custom carousel flow broken: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_custom_carousel_remix()
