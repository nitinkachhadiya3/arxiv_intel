import os
import sys
import importlib.abc
import importlib.machinery
import importlib.util
import time
from pathlib import Path

# Add project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

try:
    from dotenv import load_dotenv
    load_dotenv(root / ".env", override=True)
except ImportError:
    pass

class _PycRecoveryFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"

    def find_spec(self, fullname: str, path=None, target=None):
        if not (fullname == "src" or fullname.startswith("src.")):
            return None
        parts = fullname.split(".")
        base = self.root.joinpath(*parts)
        pkg_pyc = base / "__pycache__" / f"__init__.{self.tag}.pyc"
        mod_pyc = base.parent / "__pycache__" / f"{parts[-1]}.{self.tag}.pyc"
        if base.is_dir():
            init_py = base / "__init__.py"
            if init_py.is_file():
                return importlib.util.spec_from_file_location(fullname, str(init_py), submodule_search_locations=[str(base)])
        if len(parts) > 1:
            parent = self.root.joinpath(*parts[:-1])
            mod_py = parent / f"{parts[-1]}.py"
            if mod_py.is_file():
                loader = importlib.machinery.SourceFileLoader(fullname, str(mod_py))
                return importlib.util.spec_from_loader(fullname, loader, is_package=False)
        if pkg_pyc.is_file():
            loader = importlib.machinery.SourcelessFileLoader(fullname, str(pkg_pyc))
            return importlib.util.spec_from_loader(fullname, loader, is_package=True)
        if mod_pyc.is_file():
            loader = importlib.machinery.SourcelessFileLoader(fullname, str(mod_pyc))
            return importlib.util.spec_from_loader(fullname, loader, is_package=False)
        if base.is_dir():
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = [str(base)]
            return spec
        return None

# Activate Bytecode Recovery
sys.meta_path.insert(0, _PycRecoveryFinder(root))

# Standardize environment
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key

import cloudinary
from src.bot.core import get_fresh_previews, publish_selected
from src.bot.state import state
from src.bot.config import Config

def run_verification():
    print("🚀 Starting End-to-End Verification Flow...")
    
    # Initialize Cloudinary
    cloudinary.config(
        cloud_name=Config.CLOUDINARY_CLOUD_NAME,
        api_key=Config.CLOUDINARY_KEY,
        api_secret=Config.CLOUDINARY_SECRET
    )
    print("✅ Cloudinary initialized.")
    
    # 1. Get Fresh Previews
    print("📡 Step 1: Fetching 1 fresh topic and generating preview slides...")
    try:
        previews = get_fresh_previews(limit=1)
        if not previews:
            print("❌ No previews generated. Check logs.")
            return
        
        p = previews[0]
        p_uuid = p["uuid"]
        print(f"✅ Preview generated: {p['caption'][:60]}... (UUID: {p_uuid})")
        print(f"📂 Media URLs: {len(p['media_urls'])}")

        # 2. Publish to Instagram
        print(f"📢 Step 2: Triggering LIVE publication for UUID {p_uuid}...")
        # Note: publish_selected already handles the Cloudinary download and InstagramPublisher call
        result = publish_selected(p_uuid)
        
        media_id = result.get("instagram_media_id")
        if media_id:
            print(f"🎉 SUCCESS! Post published to Instagram.")
            print(f"📦 Media ID: {media_id}")
        else:
            print(f"❌ Publication failed or returned no Media ID. Result: {result}")

    except Exception as e:
        print(f"💥 Verification Flow Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_verification()
