import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_interesting_cricket():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Prompt for "Interesting/Unique" stories, not just scores
    prompt = (
        "Search Google for the most UNUSUAL or LEGENDARY tactical decision, player stat, or fan moment "
        "from the current / most recent IPL 2026 matches. "
        "Don't just give me the score. Find a 'Real' and 'Interesting' story. "
        "Also, decide if this story is better as a 'SINGLE_POST' (one powerful image) or 'CAROUSEL' (5 slides). "
        "Return as JSON: {'story_type': 'SINGLE_POST|CAROUSEL', 'topic': '...', 'slides': [{'type': 'IMAGE|STATS', 'text': '...', 'visual_description': '...'}], 'hashtags': '...'}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json"
            )
        )
        print("--- Interesting Cricket Story Strategy ---")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_interesting_cricket()
