import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_grounding():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Try 'gemini-2.0-flash-lite-001' or 'gemini-2.0-flash-lite'
    model_id = "gemini-2.0-flash-lite"
    
    prompt = (
        "Search Google for the latest IPL match 2026 news or standings. "
        "Provide a JSON summary with 'match', 'scores', 'result', and 'news_headline'."
    )

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
        print(f"Error: {e}")

if __name__ == "__main__":
    test_grounding()
