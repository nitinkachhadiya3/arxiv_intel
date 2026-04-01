import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_cricket():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    # Test if Gemini can fetch "live" or recent IPL 2024/2026 news using search
    prompt = "Give me a summary of the most recent IPL match or the current IPL 2026 standings and key news. Return as JSON: {\"match\": \"...\", \"summary\": \"...\", \"key_players\": [...], \"news\": \"...\"}"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", # Using 2.0 Flash for speed and grounding efficiency
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())],
                response_mime_type="application/json"
            )
        )
        print("--- Gemini Cricket Grounding Test ---")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cricket()
