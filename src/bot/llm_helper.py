import os
import json
import re
from typing import List, Tuple, Dict, Any
from google import genai
from google.genai import types

def generate_content(description: str, image_urls: List[str], category: str = "AI/Tech", draft_count: int = 2) -> Tuple[List[str], List[str]]:
    """Generate captions and image generation prompts for custom drafts using Gemini.
    Returns a tuple (captions, prompts) each of length draft_count.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Fallback to smart-mock if API key is missing
        captions = [f"{description} – Insight {i+1} ({category})" for i in range(draft_count)]
        prompts = [f"A futuristic {category.lower()} illustration, style variant {i+1}, based on user images" for i in range(draft_count)]
        return captions, prompts

    try:
        import urllib.request
        client = genai.Client(api_key=api_key)
        
        # Prepare parts for multimodal Gemini model
        parts = []
        
        # Add image URLs as parts (multimodal) - must download bytes for external URLs
        for url in image_urls[:5]: # Limit to 5
            try:
                with urllib.request.urlopen(url) as response:
                    img_data = response.read()
                    parts.append(types.Part.from_bytes(data=img_data, mime_type="image/jpeg"))
            except Exception as e:
                print(f"  ⚠ Failed to download context image {url}: {e}")

        parts.append(types.Part.from_text(text=(
            f"You are a premium AI tech content creator. A user has provided a description: '{description}' "
            f"and {len(image_urls)} images for context. "
            f"The category is '{category}'.\n\n"
            f"Task: Generate {draft_count} distinct draft versions for an Instagram carousel post. "
            f"Each version needs:\n"
            f"1. A catchy description/caption (max 150 chars).\n"
            f"2. A highly detailed image generation prompt for a futuristic tech illustration "
            f"that captures the essence of the user's input but in a different, more professional view.\n\n"
            f"Return ONLY a JSON array of objects with keys 'caption' and 'image_prompt'."
        )))

        resp = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview", # Consistent with ingestion
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
            # Ensure it matches the draft_count
            captions = [d.get("caption", f"Post variant {i}") for i, d in enumerate(data[:draft_count])]
            prompts = [d.get("image_prompt", f"Tech illustration {i}") for i, d in enumerate(data[:draft_count])]
            
            # Fill if too short
            while len(captions) < draft_count:
                captions.append(captions[-1] if captions else "Insight")
                prompts.append(prompts[-1] if prompts else "Tech art")
                
            return captions[:draft_count], prompts[:draft_count]

    except Exception as e:
        print(f"  ⚠ Gemini content generation failed: {e}")
    
    # Final fallback
    return [f"{description} (Draft {i+1})" for i in range(draft_count)], [f"Modern tech art for {category}" for i in range(draft_count)]
