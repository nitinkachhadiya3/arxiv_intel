import os
import sys
from pathlib import Path
import json

# Insert src to path
sys.path.append(os.getcwd())

def test_logo_resolution():
    # 1. Load branding.json
    p = Path("src/media/templates/branding.json")
    if not p.exists():
        print(f"❌ branding.json NOT FOUND at {p}")
        return

    with open(p, "r") as f:
        brand = json.load(f)

    # 2. Logic from gemini_carousel_images.py
    # We simulate the loading logic:
    logo_path = os.getenv("PROFILE_LOGO_PATH") or str(brand.get("logo_path", "") or "").strip()
    
    print(f"DEBUG: PROFILE_LOGO_PATH from env: {os.getenv('PROFILE_LOGO_PATH')}")
    print(f"DEBUG: logo_path from JSON: {brand.get('logo_path')}")
    print(f"--- RESOLVED logo_path: {logo_path} ---")

    # 3. Check if exists
    final_path = Path(logo_path)
    if final_path.exists() and final_path.is_file():
        print(f"✅ LOGO FOUND AND ACCESSIBLE: {final_path.absolute()}")
    else:
        print(f"❌ LOGO NOT FOUND at {logo_path}")

if __name__ == "__main__":
    test_logo_resolution()
