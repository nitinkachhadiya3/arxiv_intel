import os
from pathlib import Path

class Config:
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    BOT_MODE: str = os.getenv('BOT_MODE', 'polling')  # "polling" or "webhook"
    WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')

    # Cloudinary settings (already used elsewhere)
    CLOUDINARY_CLOUD_NAME: str = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_KEY: str = os.getenv('CLOUDINARY_KEY', '')
    CLOUDINARY_SECRET: str = os.getenv('CLOUDINARY_SECRET', '')

    # Custom post settings
    CUSTOM_POST_DRAFT_COUNT: int = int(os.getenv('CUSTOM_POST_DRAFT_COUNT', '2'))

    @classmethod
    def validate(cls) -> None:
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
