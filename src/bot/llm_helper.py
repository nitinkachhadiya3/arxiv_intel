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

        # Extract post structure if hint exists (e.g. from CricketIngestor)
        is_single = "post_type\": \"SINGLE" in description
        is_cricket = category.lower() in ("cricket", "ipl")
        
        if is_cricket:
            system_prompt = (
                f"You are a Master IPL Strategist and Creative Director. A user provided story data: '{description}' "
                f"and {len(image_urls)} context images.\n\n"
                f"Task: Generate {draft_count} versions of this IPL story.\n"
                f"CRITICAL RULES:\n"
                f"- USE SPECIFIC CRICKET TERMINOLOGY (Strike Rate, Economy, Death Overs, Powerplay).\n"
                f"- For slides marked as 'IMAGE': Generate high-impact 'Unreal Engine 5' cinematic image prompts (8K, photorealistic).\n"
                f"- For slides marked as 'STATS': Generate 'Minimalist Bokeh Sports Background' prompts that don't distract from overlaid text.\n"
                f"- Every draft must contain the exact number of slides requested in the input data (usually 1 for SINGLE, 5 for CAROUSEL).\n"
            )
        else:
            system_prompt = (
                f"You are a premium AI tech content creator and image stylist. A user provided a description: '{description}' "
                f"and {len(image_urls)} context images.\n\n"
                f"Task: Generate {draft_count} distinct 'DEEP REMIX' draft versions.\n"
                f"CRITICAL RULES:\n"
                f"- EVERY slide must be deeply dependent on the provided reference images.\n"
                f"- Generate high-fidelity image prompts inheriting the visual style of the context images.\n"
            )

        system_prompt += (
            f"EACH draft version MUST return a JSON object with a 'slides' key containing its list of slide objects.\n"
            f"Each slide object MUST have:\n"
            f"1. 'caption': A part of the reference-dependent story.\n"
            f"2. 'image_prompt': A detailed prompt for generation.\n\n"
            f"Return ONLY a JSON array of these draft objects."
        )

        parts.append(types.Part.from_text(text=system_prompt))

        resp = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.8,
                response_mime_type="application/json",
            ),
        )

        text = getattr(resp, "text", "") or ""
        m = re.search(r"\[[\s\S]*\]", text)
        if m:
            return json.loads(m.group(0))

    except Exception as e:
        print(f"  ⚠ Gemini content generation failed: {e}")
    
    # Final fallback
    return [{"slides": [{"caption": f"{description} (Draft {i+1})", "image_prompt": f"Tech illustration {i+1}"}]} for i in range(draft_count)]
