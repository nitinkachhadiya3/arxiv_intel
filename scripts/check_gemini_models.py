import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: No GEMINI_API_KEY found in .env")
    exit(1)

client = genai.Client(api_key=api_key)
try:
    for m in client.models.list():
        print(f"Model: {m.name} (Methods: {m.supported_methods})")
except Exception as e:
    print(f"Error listing models: {e}")
