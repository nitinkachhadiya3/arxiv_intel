import os
import sys
import logging
import importlib.abc
import importlib.machinery
import importlib.util
from pathlib import Path

try:
    from pathlib import Path
    from dotenv import load_dotenv
    root = Path(__file__).resolve().parent.parent.parent
    env_path = root / ".env"
    print(f"--- Environment Sync ---")
    print(f"Loading .env from: {env_path}")
    load_dotenv(env_path, override=True)
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    print(f"GEMINI_API_KEY visibility check: {gemini_key[:5]}... (len={len(gemini_key)})")
    
    # Mirror key for libraries that expect GOOGLE_API_KEY
    if gemini_key:
        os.environ["GOOGLE_API_KEY"] = gemini_key
except ImportError:
    pass

import logging
# Configure logging immediately
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Explicitly ensure GEMINI_API_KEY is available in the environment
gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
if not gemini_key:
    # Try alternate name common in this repo
    gemini_key = os.getenv("GOOGLE_API_KEY", "").strip()

if gemini_key:
    os.environ["GEMINI_API_KEY"] = gemini_key
    os.environ["GOOGLE_API_KEY"] = gemini_key # Standardize for sub-modules
    logger.info(f"✅ Gemini API Key found (len={len(gemini_key)})")
else:
    logger.warning("⚠️ GEMINI_API_KEY empty. Some flows will fail.")

# Now we can import the rest
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
from telegram.ext import ApplicationBuilder
from src.bot.config import Config
from src.bot.commands import register_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # 1. Load and validate config
    try:
        Config.validate()
        # Initialize Cloudinary
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_KEY,
            api_secret=Config.CLOUDINARY_SECRET
        )
        logger.info("✅ Cloudinary initialized.")
    except EnvironmentError as e:
        logger.error(f"Configuration error: {e}")
        return

    # 2. Build the application
    token = Config.TELEGRAM_BOT_TOKEN
    app = ApplicationBuilder().token(token).build()

    # 3. Register command and message handlers
    register_handlers(app)

    # 4. Start the bot
    mode = Config.BOT_MODE.lower()
    
    if mode == "webhook":
        webhook_url = Config.WEBHOOK_URL
        if not webhook_url:
            logger.error("BOT_MODE is set to 'webhook' but WEBHOOK_URL is missing.")
            return
        
        webhook_url = webhook_url.rstrip("/")
        logger.info(f"Starting bot in WEBHOOK mode at {webhook_url}")
        # In a real deployment, you'd specify listen address and port here
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8443)),
            url_path=token,
            webhook_url=f"{webhook_url}/{token}"
        )
    else:
        logger.info("Starting bot in POLLING mode...")
        app.run_polling()

if __name__ == "__main__":
    main()
