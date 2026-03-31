import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(".env")

# Ensure PYTHONPATH is set so we can import src
import sys
sys.path.append(os.getcwd())

from src.bot.core import get_fresh_previews

def test_get_posts_safety():
    print("Testing 'Get Posts' (Safety/Text-only) flow...")
    try:
        # This should trigger a standard 1-item preview generation without any reference images
        previews = get_fresh_previews(limit=1)
        print(f"Successfully generated {len(previews)} preview(s).")
        for p in previews:
            print(f"Caption: {p['caption'][:100]}...")
            print(f"Media URLs: {p['media_urls']}")
        print("✅ SUCCESS: 'Get Posts' flow is unaffected.")
    except Exception as e:
        print(f"❌ FAILED: 'Get Posts' flow broken: {e}")

if __name__ == "__main__":
    test_get_posts_safety()
