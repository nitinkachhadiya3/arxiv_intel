import os
import urllib.request
import tempfile
import uuid
from typing import List, Dict, Any
from pathlib import Path

from src.publish.instagram_publisher import InstagramPublisher
from src.media.image_generator import CarouselImageGenerator
from src.bot.cloudinary_uploader import CloudinaryUploader
from src.bot.llm_helper import generate_content
from src.bot.config import Config
from src.bot.state import state
from src.utils.config import get_config

# Helper to fetch fresh topics using existing pipeline
def _fetch_fresh_topics(limit: int = 5) -> List[Dict[str, Any]]:
    # We need to ensure the bytecode recovery finder is active if importing from src.*
    from src.ingestion.topic_picker import pick_fresh_topic
    topics = []
    seen_headlines = set()
    
    # Try more than 'limit' times to find unique topics if some are duplicates
    max_attempts = limit * 3
    attempts = 0
    
    while len(topics) < limit and attempts < max_attempts:
        attempts += 1
        try:
            t = pick_fresh_topic()
            if not t or not t.get("topic"):
                continue
            
            headline = t["topic"].strip().lower()
            if headline in seen_headlines:
                continue
                
            seen_headlines.add(headline)
            topics.append(t)
        except Exception as e:
            print(f"⚠ Failed to fetch fresh topic: {e}")
            
    return topics

def get_fresh_previews(limit: int = None) -> List[Dict[ Any, Any]]:
    """Return preview objects for the *Get Posts* flow."""
    # Fail-safe environment seeding
    if not os.getenv("GEMINI_API_KEY"):
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env", override=True)
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if key:
            os.environ["GOOGLE_API_KEY"] = key
            
    if limit is None:
        limit = Config.CUSTOM_POST_DRAFT_COUNT
        
    previews = []
    topics = _fetch_fresh_topics(limit)
    generator = CarouselImageGenerator()
    
    for topic in topics:
        topic_title = topic.get('topic', 'Tech Update')
        slug = f"preview_{uuid.uuid4().hex[:8]}"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            media_paths = generator.render_topic_slides(
                topic_slug=slug,
                slide_texts=topic.get('slides', [topic_title]),
                out_dir=out_dir,
                topic_title=topic_title,
                cover_headline=topic_title,
                visual_prompts=topic.get('visual_prompts', []),
                story_post=topic
            )
            
            media_urls = [CloudinaryUploader.upload_file(str(p)) for p in media_paths]
            
        preview_uuid = str(uuid.uuid4())
        preview = {
            "uuid": preview_uuid,
            "caption": f"{topic_title}\n\n{topic.get('hashtags', '')}",
            "media_urls": media_urls,
        }
        previews.append(preview)
        state.update_child("previews", preview_uuid, preview)
    return previews

def generate_custom_previews(description: str, user_image_urls: List[str]) -> List[Dict[str, Any]]:
    """Generate drafts for the *Custom Post* flow.
    Returns a list of draft dicts with keys: uuid, caption, media_urls.
    """
    # Fail-safe environment seeding
    if not os.getenv("GEMINI_API_KEY"):
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env", override=True)
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if key:
            os.environ["GOOGLE_API_KEY"] = key
            
    draft_count = Config.CUSTOM_POST_DRAFT_COUNT
    # Truncate description to prevent token limit errors
    safe_desc = description[:10000] if len(description) > 10000 else description
    captions, prompts = generate_content(safe_desc, user_image_urls, draft_count=draft_count)
    generator = CarouselImageGenerator()
    drafts = []
    
    for i in range(draft_count):
        draft_uuid = str(uuid.uuid4())
        slug = f"custom_{draft_uuid[:8]}"
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            # Use the generated caption and prompt for rendering
            media_paths = generator.render_topic_slides(
                topic_slug=slug,
                slide_texts=[captions[i]],
                out_dir=out_dir,
                topic_title=description[:50],
                cover_headline=captions[i],
                visual_prompts=[prompts[i]]
            )
            media_urls = [CloudinaryUploader.upload_file(str(p)) for p in media_paths]
            
        draft = {
            "uuid": draft_uuid,
            "caption": captions[i],
            "media_urls": media_urls,
        }
        drafts.append(draft)
        state.update_child("custom", draft_uuid, draft)
    return drafts

def _download_from_cloudinary(url: str, dest_dir: str) -> str:
    """Download a Cloudinary image to `dest_dir` and return the local file path."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(url.split('?')[0])
    if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        filename += ".jpg"
    local_path = os.path.join(dest_dir, filename)
    urllib.request.urlretrieve(url, local_path)
    return local_path

import time

def wait_for_generation(job_id, check_func, max_retries=10, delay=10):
    """
    Robust polling utility to wait for a background task. 
    Implements a delay to prevent terminal flooding.
    """
    retries = 0
    while retries < max_retries:
        status = check_func(job_id)
        if status == "completed":
            return True
        elif status == "failed":
            print("Generation failed.")
            return False
            
        print(f"Status check {retries+1}/{max_retries}...")
        time.sleep(delay) 
        retries += 1
        
    print("Timed out.")
    return False

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
        cfg = get_config()
        publisher = InstagramPublisher(cfg)
        
        if len(local_paths) > 1:
            result = publisher.publish_carousel_from_paths([Path(p) for p in local_paths], item.get("caption", ""))
        else:
            result = publisher.publish_single_image_from_path(local_paths[0], item.get("caption", ""))
        return result
