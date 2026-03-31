import os
import io
import urllib.request
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv(".env")

def test_image_to_image():
    api_key = os.getenv("GEMINI_API_KEY")
    # We'll use the primary image model from .env if possible
    model_id = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.1-flash-image")
    
    client = genai.Client(api_key=api_key)
    
    # Reference image: A professional man in a suit (Unsplash)
    ref_url = "https://techstartups.com/wp-content/uploads/2020/06/Big-Tech-CEOs.jpg"
    
    print(f"Downloading reference image from {ref_url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(ref_url, headers=headers)
    with urllib.request.urlopen(req) as response:
        img_data = response.read()
    
    prompt = "A high-end, cinematic editorial portrait of this professional man in a futuristic cyberpunk office, neon accents, dramatic shadows, 8k resolution."
    
    print(f"Generating image using {model_id} with reference image...")
    
    parts = [
        types.Part.from_bytes(data=img_data, mime_type="image/jpeg"),
        types.Part.from_text(text=prompt)
    ]
    
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="3:4"),
    )
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[types.Content(role="user", parts=parts)],
            config=config,
        )
        
        image = None
        candidates = getattr(response, "candidates", None) or []
        for cand in candidates:
            c = getattr(cand, "content", None)
            p_list = getattr(c, "parts", None) or []
            for p in p_list:
                id_data = getattr(p, "inline_data", None)
                if id_data is not None:
                    image = Image.open(io.BytesIO(id_data.data)).convert("RGB")
                    break
        
        if image:
            print("Successfully generated image!")
            image.save("test_output_reference.jpg")
            print("Saved to test_output_reference.jpg")
        else:
            print("No image returned in response.")
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Error during generation: {e}")

if __name__ == "__main__":
    test_image_to_image()
