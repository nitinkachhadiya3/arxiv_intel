import os
import json
import logging
from dotenv import load_dotenv
from src.ingestion.cricket_ingestor import pick_best_cricket_topic

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_cricket_ingestion():
    print("🏏 [TEST] Starting IPL 2026 Ingestion Test...")
    topic_data = pick_best_cricket_topic()
    
    if topic_data and topic_data.get("topic"):
        print("\n✅ Successfully fetched IPL news!")
        print(f"Topic: {topic_data['topic']}")
        print(f"Source: {topic_data.get('content_source', 'N/A')}")
        print("\nSlides Drafted:")
        for i, slide in enumerate(topic_data.get("slides", []), 1):
            print(f"  Slide {i}: {slide}")
    else:
        print("\n❌ Failed to fetch IPL news.")

if __name__ == "__main__":
    test_cricket_ingestion()
