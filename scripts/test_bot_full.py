import os
import sys
import importlib.abc
import importlib.machinery
import importlib.util
from pathlib import Path
from types import ModuleType

# Add the project root to sys.path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

try:
    from dotenv import load_dotenv
    load_dotenv(root / ".env")
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

import cloudinary
from src.bot.config import Config
from src.bot.core import get_fresh_previews, generate_custom_previews
from src.bot.cloudinary_uploader import CloudinaryUploader

def test_bot_flows():
    print("🚀 Starting Bot Logic Test...")
    
    # 1. Validate Config
    try:
        Config.validate()
        print("✅ Config validated.")
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
        return

    # 2. Setup Cloudinary (existing logic in app usually handles this via env)
    cloudinary.config(
        cloud_name=Config.CLOUDINARY_CLOUD_NAME,
        api_key=Config.CLOUDINARY_KEY,
        api_secret=Config.CLOUDINARY_SECRET
    )

    # 3. Test Get Posts Flow
    print("\n--- Testing 'Get Posts' Flow (Limit 1) ---")
    try:
        previews = get_fresh_previews(limit=1)
        print(f"✅ Generated {len(previews)} previews.")
        for i, p in enumerate(previews):
            print(f"  Post {i+1}:")
            print(f"    UUID: {p['uuid']}")
            print(f"    Caption: {p['caption'][:100]}...")
            print(f"    Images: {len(p['media_urls'])} URLs")
            for url in p['media_urls']:
                print(f"      - {url}")
    except Exception as e:
        print(f"❌ Get Posts flow failed: {e}")

    # 4. Test Custom Post Flow
    print("\n--- Testing 'Custom Post' Flow ---")
    sample_desc = "The evolution of Agentic AI: How autonomous systems are transforming enterprise workflows in 2026."
    # Use an existing image from the repo as a sample
    sample_img_path = "/Users/nitinkaachhadiya/social_agent/arxiv_intel/output/images/tech_sora_shutdown/slide_01.jpg"
    
    try:
        print(f"📸 Uploading sample image: {sample_img_path}")
        sample_img_url = CloudinaryUploader.upload_file(sample_img_path)
        print(f"✅ Sample image uploaded: {sample_img_url}")
        
        print(f"🤖 Calling Gemini for custom drafts...")
        drafts = generate_custom_previews(sample_desc, [sample_img_url])
        print(f"✅ Generated {len(drafts)} custom drafts.")
        for i, d in enumerate(drafts):
            print(f"  Draft {i+1}:")
            print(f"    UUID: {d['uuid']}")
            print(f"    Caption: {d['caption']}")
            print(f"    Images: {len(d['media_urls'])} URLs")
            for url in d['media_urls']:
                print(f"      - {url}")
    except Exception as e:
        print(f"❌ Custom Post flow failed: {e}")

if __name__ == "__main__":
    test_bot_flows()
