import os
import urllib.request
import tempfile
from typing import List, Dict, Any

from src.publish.instagram_publisher import InstagramPublisher
from src.media.editorial_compositor import compose_carousel
from src.bot.cloudinary_uploader import CloudinaryUploader
from src.bot.llm_helper import generate_content
from src.bot.config import Config
from src.bot.state import state

# Helper to fetch fresh topics using existing pipeline
def _fetch_fresh_topics(limit: int = 5) -> List[Dict[str, Any]]:
    from src.ingestion.topic_picker import pick_fresh_topic
    topics = []
    for _ in range(limit):
        try:
            topics.append(pick_fresh_topic())
        except Exception as e:
            print(f"⚠ Failed to fetch fresh topic: {e}")
    return topics

def get_fresh_previews() -> List[Dict[str, Any]]:
    """Return 5 preview objects for the *Get Posts* flow.
    Each preview dict contains: uuid, caption, media_urls (list of Cloudinary URLs).
    """
    previews = []
    topics = _fetch_fresh_topics(5)
    for topic in topics:
        media_paths = compose_carousel(topic)  # local image files
        media_urls = [CloudinaryUploader.upload_file(p) for p in media_paths]
        preview_uuid = str(uuid.uuid4())
        preview = {
            "uuid": preview_uuid,
            "caption": f"{topic.get('topic', '')}\n{topic.get('hashtags', '')}",
            "media_urls": media_urls,
        }
        previews.append(preview)
        state["previews"][preview_uuid] = preview
    return previews

def generate_custom_previews(description: str, user_image_urls: List[str]) -> List[Dict[str, Any]]:
    """Generate drafts for the *Custom Post* flow.
    Returns a list of draft dicts with keys: uuid, caption, media_urls.
    """
    draft_count = Config.CUSTOM_POST_DRAFT_COUNT
    captions, prompts = generate_content(description, user_image_urls, draft_count=draft_count)
    drafts = []
    for i in range(draft_count):
        synthetic_topic = {
            "topic": description,
            "slides": [f"Slide {j+1}" for j in range(4)],
            "hashtags": "#AI #Tech",
            "content_source": "custom",
        }
        # In a real implementation we would use prompts[i] to generate images.
        media_paths = compose_carousel(synthetic_topic)
        media_urls = [CloudinaryUploader.upload_file(p) for p in media_paths]
        draft_uuid = str(uuid.uuid4())
        draft = {
            "uuid": draft_uuid,
            "caption": captions[i],
            "media_urls": media_urls,
        }
        drafts.append(draft)
        state["custom"][draft_uuid] = draft
    return drafts

def _download_from_cloudinary(url: str, dest_dir: str) -> str:
    """Download a Cloudinary image to `dest_dir` and return the local file path."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(url.split('?')[0])
    local_path = os.path.join(dest_dir, filename)
    urllib.request.urlretrieve(url, local_path)
    return local_path

def publish_selected(preview_uuid: str) -> Dict[str, Any]:
    """Publish a preview or custom draft to Instagram.
    Looks up the preview/draft in the in‑memory state, downloads the images
    from Cloudinary to temporary files, and calls InstagramPublisher.
    Returns the response dict from the publisher.
    """
    if preview_uuid in state.get("custom", {}):
        item = state["custom"][preview_uuid]
    elif preview_uuid in state.get("previews", {}):
        item = state["previews"][preview_uuid]
    else:
        raise ValueError(f"Preview with uuid {preview_uuid} not found in state")

    # Download images to a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_paths = [_download_from_cloudinary(url, tmp_dir) for url in item["media_urls"]]
        publisher = InstagramPublisher()
        result = publisher.publish_carousel_from_paths(local_paths, item.get("caption", ""))
        return result
