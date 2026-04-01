import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_grounding():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Try the standard flash model name
    prompt = (
        "Search Google and provide a short summary of the current IPL 2026 match or latest standings. "
        "Include scores and 2 key players. Return as JSON: "
        "{'match': '...', 'scores': '...', 'summary': '...', 'players': []}"
    )
    
    # We'll try 'gemini-2.0-flash' which is the current flagship fast model
    model_id = "gemini-2.0-flash"
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())],
                response_mime_type="application/json"
            )
        )
        print(f"--- IPL Grounding Result ({model_id}) ---")
        print(response.text)
    except Exception as e:
        print(f"Error testing {model_id}: {e}")

if __name__ == "__main__":
    test_grounding()
