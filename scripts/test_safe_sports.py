import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_safe_worlds():
    print("🏏 [TEST] Verifying Safe Sports Visuals...")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    client = genai.Client(api_key=api_key)
    
    # Models to test
    model_id = os.getenv("GEMINI_IMAGE_MODEL", "imagen-3")
    print(f"📡 Using model: {model_id}")

    # The 3 new "Safe" prompts
    prompts = [
        # Stadium (No crowd)
        "Epic wide-angle photograph of a modern cricket stadium at night during an IPL match. "         "Brilliant floodlights creating a hazy atmospheric glow, a perfectly manicured green pitch. "         "Professional sports photography, 16-35mm lens. No people visible.",
        
        # Gear (Still Life)
        "Premium editorial still-life photograph of cricket equipment. A high-end cricket bat "         "leaning against three wooden stumps on a perfectly cut green grass pitch. "         "Cinematic side-lighting, long shadows, shallow depth of field.",
        
        # Silhouette
        "A powerful, high-contrast silhouette of a cricket player in a dynamic action pose. "         "The player is a dark, unidentifiable shape against the brilliant white glow of stadium "         "floodlights. Dramatic lens flare, no faces visible."
    ]

    for i, p in enumerate(prompts):
        print(f"\n�� Testing Prompt {i+1}: {p[:100]}...")
        try:
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="3:4"),
            )
            response = client.models.generate_content(
                model=model_id,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=p)])],
                config=config,
            )
            
            # Check for image
            found = False
            for cand in (response.candidates or []):
                for part in (cand.content.parts or []):
                    if part.inline_data:
                        print(f"✅ SUCCESS: Image generated for Prompt {i+1}!")
                        found = True
                        break
            if not found:
                print(f"❌ FAILURE: No image bytes in response for Prompt {i+1}.")
                
        except Exception as e:
            print(f"❌ ERROR for Prompt {i+1}: {e}")

if __name__ == "__main__":
    test_safe_worlds()
