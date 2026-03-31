import os
import asyncio
from dotenv import load_dotenv

# Load environment to ensure GEMINI_API_KEY is available
load_dotenv(".env")

from src.bot.llm_helper import generate_content

def run_test():
    # A reference of a high-end tech workspace/lifestyle shot
    test_image_url = "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&q=80"
    description = "Remix this minimalist tech setup. I want the same vibe but more cinematic and with better lighting."
    
    print(f"Testing Gemini AI REMIXER (Custom Post)...")
    print(f"User Description/Request: {description}")
    print(f"Reference Image URL: {test_image_url}")
    print("-" * 50)
    
    # We pass category "AI/Tech" and just generate 1 draft for testing
    captions, prompts = generate_content(
        description=description,
        image_urls=[test_image_url],
        category="Tech Lifestyle",
        draft_count=1
    )
    
    print("RESULTS:")
    for i in range(len(captions)):
        print(f"\nDraft {i+1}:")
        print(f"CAPTION: {captions[i]}")
        print(f"PROMPT:  {prompts[i]}")

if __name__ == "__main__":
    run_test()
