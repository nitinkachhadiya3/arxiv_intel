import os
import sys
import uuid
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from dotenv import load_dotenv
load_dotenv(root / ".env", override=True)

from src.bot.core import generate_custom_previews
from src.bot.state import state

def test_human_vision():
    print(f"�� Starting Human Vision Test...")
    
    # Input description and reference image
    description = "A successful tech founder in a sleek corporate office, looking confident."
    # Using a professional-looking portrait from Unsplash
    image_urls = ["https://images.unsplash.com/photo-1560250097-0b93528c311a?q=80&w=600&auto=format&fit=crop"]
    
    print(f"✍️ Description: {description}")
    print(f"📸 Reference Image: {image_urls[0]}")
    
    try:
        # This will trigger Gemini Vision -> Image Generation
        drafts = generate_custom_previews(description, image_urls)
        
        print(f"✅ Successfully generated {len(drafts)} draft(s).")
        
        for i, draft in enumerate(drafts, 1):
            print(f"\n--- Draft {i} ---")
            print(f"UUID: {draft['uuid']}")
            print(f"Caption: {draft['caption']}")
            print(f"Media URLs:")
            for url in draft['media_urls']:
                print(f"  🔗 {url}")
                
        print("\n✨ VISION TEST SUCCESSFUL.")
        
    except Exception as e:
        print(f"❌ Vision Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_human_vision()
