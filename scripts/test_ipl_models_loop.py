import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# The models we will try for grounding
MODELS_TO_TRY = [
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-3.1-flash-lite-preview"
]

def test_grounding():
    prompt = "Search Google for the latest IPL 2026 match summary or standings. Return JSON: {'match': '...', 'result': '...'}"
    
    for model_id in MODELS_TO_TRY:
        print(f"📡 Testing Grounding on model: {model_id}")
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())],
                    response_mime_type="application/json"
                )
            )
            print(f"✅ SUCCESS with {model_id}!")
            print(response.text)
            return model_id
        except Exception as e:
            print(f"❌ FAILED {model_id}: {e}")
    return None

if __name__ == "__main__":
    working_model = test_grounding()
    if working_model:
        print(f"\n�� BEST working model for grounding: {working_model}")
