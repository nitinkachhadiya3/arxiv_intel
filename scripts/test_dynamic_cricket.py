import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_dynamic():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = (
        "Find ONE highly interesting tactical aspect or unusual milestone from IPL 2026 matches today/this week. "
        "Decide if it fits as a SINGLE_POST or a 5-slide CAROUSEL. "
        "If CAROUSEL, mark which slides need an IMAGE and which are just STATS (text-heavy). "
        "Return as JSON: {'post_type': 'SINGLE|CAROUSEL', 'topic': '...', 'slides': [{'type': 'IMAGE|STATS', 'content': '...'}], 'hashtags': '...'}"
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
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dynamic()
