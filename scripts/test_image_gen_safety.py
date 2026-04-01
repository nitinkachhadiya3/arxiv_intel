import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io

load_dotenv()
logging.basicConfig(level=logging.INFO)

def test_gen(prompt):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    client = genai.Client(api_key=api_key)
    
    # Try gemini-3.1-flash-image-preview (as in .env)
    model_id = "gemini-3.1-flash-image-preview"
    
    print(f"\n🚀 Testing Prompt: {prompt[:100]}...")
    try:
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="3:4"),
        )
        response = client.models.generate_content(
            model=model_id,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
            config=config,
        )
        # Check if image returned
        for cand in (response.candidates or []):
            for part in (cand.content.parts or []):
                if part.inline_data:
                    print("✅ SUCCESS: Image generated!")
                    return True
        print("❌ FAILURE: No image bytes in response.")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test 1: The likely culprit (Action with specific athlete mentions/silhouettes)
    p1 = ("Professional sports action photograph of a cricket match. Focus on a single dynamic "
          "moment: a batsman mid-swing with a blurred ball. Saturated green grass, "
          "white leather ball texture. Low-angle perspective, fast shutter speed freezing the action.")
    
    # Test 2: Safer Environment focus
    p2 = ("Epic wide-angle photograph of a modern cricket stadium at night. "
          "Brilliant floodlights creating a hazy atmospheric glow, a perfectly manicured green pitch, "
          "no people visible.")

    test_gen(p1)
    test_gen(p2)
