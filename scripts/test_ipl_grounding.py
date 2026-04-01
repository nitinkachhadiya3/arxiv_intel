import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_grounding():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # We use Flash 2.0 (latest) which is perfect for real-time grounding
    prompt = (
        "Provide a summary of the latest IPL match from today or the current week in 2026. "
        "Include scores, key players, and match result. "
        "Format as JSON: {'match': 'Team A vs Team B', 'result': '...', 'summary': '...', 'top_performers': []}"
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())],
                response_mime_type="application/json"
            )
        )
        print("--- IPL Grounding Result ---")
        print(response.text)
    except Exception as e:
        print(f"Error testing grounding: {e}")

if __name__ == "__main__":
    test_grounding()
