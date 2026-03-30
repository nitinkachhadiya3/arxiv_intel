import os
from pathlib import Path

class Config:
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        return os.getenv('TELEGRAM_BOT_TOKEN', '')

    @property
    def TELEGRAM_CHAT_ID(self) -> str:
        return os.getenv('TELEGRAM_CHAT_ID', '')

    @property
    def BOT_MODE(self) -> str:
        return os.getenv('BOT_MODE', 'polling').lower()

    @property
    def WEBHOOK_URL(self) -> str:
        return os.getenv('WEBHOOK_URL', '')

    @property
    def CLOUDINARY_CLOUD_NAME(self) -> str:
        return os.getenv('CLOUDINARY_CLOUD_NAME', '')

    @property
    def CLOUDINARY_KEY(self) -> str:
        return os.getenv('CLOUDINARY_KEY', '')

    @property
    def CLOUDINARY_SECRET(self) -> str:
        return os.getenv('CLOUDINARY_SECRET', '')

    @property
    def CUSTOM_POST_DRAFT_COUNT(self) -> int:
        return int(os.getenv('CUSTOM_POST_DRAFT_COUNT', '2'))

    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv('GEMINI_API_KEY', '')

    @classmethod
    def validate(cls) -> None:
        instance = cls()
        missing = []
        if not instance.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not instance.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")

# Instantiate for use
Config = Config()
