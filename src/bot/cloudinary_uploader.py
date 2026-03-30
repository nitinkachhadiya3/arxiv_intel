import os
import logging
import cloudinary
from cloudinary import uploader
from src.bot.config import Config

logger = logging.getLogger(__name__)

class CloudinaryUploader:
    @staticmethod
    def upload_file(file_path: str, folder: str = 'telegram_bot'):
        """Upload a local file to Cloudinary and return the secure URL.
        Args:
            file_path: Path to the local file.
            folder: Cloudinary folder name.
        Returns:
            The secure URL of the uploaded asset.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Self-configure if needed
        if not cloudinary.config().api_key:
            cloudinary.config(
                cloud_name=Config.CLOUDINARY_CLOUD_NAME,
                api_key=Config.CLOUDINARY_KEY,
                api_secret=Config.CLOUDINARY_SECRET
            )
        
        c = cloudinary.config()
        logger.info(f"📤 Cloudinary Upload Start: {file_path}")
        logger.info(f"   Cloud Name: {c.cloud_name}")
        logger.info(f"   API Key: {str(c.api_key)[:5]}... (len={len(str(c.api_key)) if c.api_key else 0})")

        result = uploader.upload(file_path, folder=folder, resource_type='image')
        return result.get('secure_url')
