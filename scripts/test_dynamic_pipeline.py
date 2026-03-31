import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.ingestion.cricket_ingestor import pick_best_cricket_topic
from src.bot.core import get_fresh_previews

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pipeline():
    print("🚀 [TEST] Starting Dynamic IPL Pipeline Test...")
    
    # 1. Test Ingestion
    print("\n📡 Step 1: Ingesting Interesting Topic...")
    topic = pick_best_cricket_topic()
    if not topic:
        print("❌ Ingestion failed.")
        return
    
    print(f"✅ Ingested: {topic['topic']} (Type: {topic.get('post_type', 'CAROUSEL')})")
    
    # 2. Test Multi-Format Previews
    print("\n🎨 Step 2: Generating Previews (Rendering)...")
    # We'll mock the _fetch_fresh_topics to return our specific topic
    import src.bot.core as core
    original_fetch = core._fetch_fresh_topics
    core._fetch_fresh_topics = lambda limit: [topic]
    
    try:
        previews = get_fresh_previews(limit=1)
        if previews:
            p = previews[0]
            print(f"✅ Generation Successful!")
            print(f"UUID: {p['uuid']}")
            print(f"Media URLs: {len(p['media_urls'])} files generated.")
            for i, url in enumerate(p['media_urls']):
                print(f"  Slide {i+1}: {url}")
        else:
            print("❌ No previews generated.")
    finally:
        core._fetch_fresh_topics = original_fetch

if __name__ == "__main__":
    test_pipeline()
