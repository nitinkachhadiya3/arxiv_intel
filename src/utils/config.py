import os
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AppConfig:
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip())
    gemini_image_model: str = field(default_factory=lambda: os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.0-flash-exp").strip())
    gemini_image_aspect_ratio: str = field(default_factory=lambda: os.getenv("GEMINI_IMAGE_ASPECT_RATIO", "3:4").strip())
    gemini_image_size: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_IMAGE_SIZE"))

def get_config() -> AppConfig:
    return AppConfig()
