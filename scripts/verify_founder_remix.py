import os
from dotenv import load_dotenv
from pathlib import Path
import sys

load_dotenv(".env")
sys.path.append(os.getcwd())

from src.bot.core import generate_custom_previews

def test_founder_remix():
    print("Testing 'Custom Post' (Multimodal/Image-to-Image) flow...")
    
    # 5 Unsplash Professional Portrait URLs for testing
    # These represent our 'founders' for the remix test
    founder_urls = [
        "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=800&q=80",
        "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&q=80",
        "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800&q=80",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&q=80"
    ]
    
    description = "Remix this meeting of the legends. Create a professional cinematic poster featuring these founders discussing the future of AI in a sleek boardroom."
    
    try:
        # This should trigger the new multimodal logic with img_parts passed to Imagen 3
        # We generate 1 draft for testing speed
        drafts = generate_custom_previews(description, founder_urls)
        
        print(f"Successfully generated {len(drafts)} custom draft(s).")
        for d in drafts:
            print(f"Caption: {d['caption'][:100]}...")
            print(f"Media URLs: {d['media_urls']}")
        
        print("✅ SUCCESS: 'Founder Remix' flow with multimodal injection completed.")
    except Exception as e:
        print(f"❌ FAILED: 'Founder Remix' flow broken: {e}")

if __name__ == "__main__":
    test_founder_remix()
