import os
from cloudinary import uploader
from cloudinary.utils import cloud_name

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
        result = uploader.upload(file_path, folder=folder, resource_type='image')
        return result.get('secure_url')
