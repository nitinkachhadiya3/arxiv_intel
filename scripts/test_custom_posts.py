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

def test_custom_post():
    print(f"🚀 Starting Custom Post test in {root}")
    
    # Sample input
    description = "A futuristic city built on floating islands with AI-controlled traffic."
    # Using a reliable placeholder image URL
    image_urls = ["https://picsum.photos/seed/picsum/800/1000"]
    
    print(f"✍️ Description: {description}")
    print(f"📸 Image context: {image_urls[0]}")
    print("📡 Step 1: Generating custom drafts (this uses Gemini)...")
    
    try:
        drafts = generate_custom_previews(description, image_urls)
        
        print(f"✅ Successfully generated {len(drafts)} draft(s).")
        
        for i, draft in enumerate(drafts, 1):
            print(f"\n--- Draft {i} ---")
            print(f"ID: {draft['uuid']}")
            print(f"Caption: {draft['caption']}")
            print(f"Media URLs ({len(draft['media_urls'])}):")
            for url in draft['media_urls']:
                print(f"  🔗 {url}")
                
        print("\n✨ Test completed successfully!")
        print("Note: Instagram publication was NOT triggered as per instructions.")
        print("RESULT: SUCCESS")
        
    except Exception as e:
        print(f"❌ Error during Custom Post test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_custom_post()
