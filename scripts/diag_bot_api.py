import os
import sys
import importlib.abc
import importlib.machinery
import importlib.util
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

print(f"--- Global Context ---")
gemini_key = os.getenv("GEMINI_API_KEY", "MISSING")
print(f"OS GEMINI_API_KEY: {gemini_key[:10]}... (len={len(gemini_key)})")

try:
    from src.utils.config import get_config
    cfg = get_config()
    cfg_key = getattr(cfg, "gemini_api_key", "MISSING")
    print(f"Config object GEMINI_API_KEY: {cfg_key[:10]}... (len={len(str(cfg_key))})")
except Exception as e:
    print(f"Error loading config: {e}")

try:
    from src.bot.core import _fetch_fresh_topics
    print(f"Imported src.bot.core successfully.")
except Exception as e:
    print(f"Error importing src.bot.core: {e}")

try:
    from src.content.story_brief import generate_story_brief
    print(f"Imported src.content.story_brief successfully.")
except Exception as e:
    print(f"Error importing src.content.story_brief: {e}")

try:
    from src.media.image_generator import CarouselImageGenerator
    print(f"Imported src.media.image_generator successfully.")
except Exception as e:
    print(f"Error importing src.media.image_generator: {e}")

print(f"--- Final Visibility Check ---")
import os
print(f"Final OS GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'MISSING')[:10]}...")
