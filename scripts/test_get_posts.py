import sys
import os
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

print(f"🚀 Starting Get Post test in {root}")

from src.bot.core import get_fresh_previews
from src.bot.config import Config

def test_fetch():
    print("📡 Step 1: Triggering get_fresh_previews(limit=1)...")
    try:
        # Override the limit if needed via Config but we pass it directly
        previews = get_fresh_previews(limit=1)
        
        if not previews:
            print("❌ No previews were generated.")
            return

        print(f"✅ Successfully generated {len(previews)} preview(s).")
        for i, preview in enumerate(previews):
            print(f"\n--- Preview {i+1} ---")
            print(f"ID: {preview['uuid']}")
            print(f"Caption: {preview['caption'][:100]}...")
            print(f"Media URLs ({len(preview['media_urls'])}):")
            for url in preview['media_urls']:
                print(f"  🔗 {url}")
        
        print("\n✨ Test completed successfully!")
    except Exception as e:
        print(f"❌ Error during Get Post test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch()
