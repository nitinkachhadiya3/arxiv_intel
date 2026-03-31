import os
import json
import re
from typing import List, Tuple, Dict, Any
from google import genai
from google.genai import types

def generate_content(description: str, image_urls: List[str], category: str = "AI/Tech", draft_count: int = 2) -> List[Dict[str, Any]]:
    """Generate multi-slide carousel drafts using Gemini.
    Returns a list of drafts, each being a dict with: 'slides': List[{'caption', 'image_prompt'}]
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Fallback to smart-mock if API key is missing
        return [{"slides": [{"caption": f"{description} (Draft {i+1})", "image_prompt": f"Tech illustration {i+1}"}]} for i in range(draft_count)]

    try:
        import urllib.request
        client = genai.Client(api_key=api_key)
        
        # Prepare parts for multimodal Gemini model
        parts = []
        
        # Add image URLs as parts (multimodal) - limit to 5
        for url in image_urls[:5]:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    img_data = response.read()
                    parts.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))
            except Exception as e:
                print(f"  ⚠ Failed to download context image {url}: {e}")

        parts.append(types.Part.from_text(text=(
            f"You are a premium AI tech content creator and image stylist. A user has provided a description: '{description}' "
            f"and {len(image_urls)} images for context which should be treated as a Visual Reference/Screenshot.\n\n"
            f"Task: Analyze the 'Visual DNA' of the provided images (subject, style, layout, tone). "
            f"Generate {draft_count} distinct 'REMIXED' draft versions for an Instagram carousel. "
            f"The goal is to keep the same context/topic as the reference but provide a 'Hero Remix' on Slide 1 followed by 'Value Content' slides.\n\n"
            f"EACH draft version MUST contain 3 to 5 slides:\n"
            f"- SLIDE 1 (HERO REMIX): A professional, direct remix of the visual DNA of the provided reference. Treat this as the hook.\n"
            f"- SLIDES 2-5 (CONTENT): Informative/Value-adding slides that expand on the user's description with tips, insights, or details.\n\n"
            f"For each slide, provide:\n"
            f"1. A catchy caption (max 150 chars).\n"
            f"2. A highly detailed image generation prompt. Rule: Slide 1 MUST focus on the reference style. Slides 2-5 can be consistent or supplementary.\n\n"
            f"Return ONLY a JSON array of objects, one for each draft version. Each object must have a 'slides' key containing its list of slide objects with keys 'caption' and 'image_prompt'."
        )))

        resp = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.8,
                response_mime_type="application/json",
            ),
        )

        text = getattr(resp, "text", "") or ""
        # Clean up JSON if model adds markdown
        m = re.search(r"\[[\s\S]*\]", text)
        if m:
            data = json.loads(m.group(0))
            # Ensure it's a list of drafts
            drafts = []
            for d in data[:draft_count]:
                if "slides" in d and isinstance(d["slides"], list):
                    drafts.append(d)
                else:
                    # Fallback if structure is wrong
                    drafts.append({"slides": [{"caption": "Post Draft", "image_prompt": "Tech news image"}]})
            return drafts

    except Exception as e:
        print(f"  ⚠ Gemini content generation failed: {e}")
    
    # Final fallback
    return [{"slides": [{"caption": f"{description} (Draft {i+1})", "image_prompt": f"Tech illustration {i+1}"}]} for i in range(draft_count)]
