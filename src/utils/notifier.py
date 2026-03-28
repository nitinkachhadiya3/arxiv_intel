"""
Telegram Notifier — Sends success/error alerts to your phone.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.
"""
from __future__ import annotations

import os
import requests
from typing import Optional


def send_telegram_message(message: str) -> bool:
    """Send a raw text message via Telegram Bot API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        # Silent skip if not configured, to avoid crashing the pipeline
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  ⚠ Telegram Notification Failed: {e}")
        return False


def notify_success(topic: str, source: str, media_id: Optional[str] = None):
    """Notify that a post was successfully published."""
    msg = (
        f"<b>✅ ArxivIntel: Post Published</b>\n\n"
        f"<b>Topic:</b> {topic}\n"
        f"<b>Source:</b> <code>{source}</code>\n"
    )
    if media_id:
        msg += f"<b>Media ID:</b> <code>{media_id}</code>\n"
    
    msg += f"\n🕒 {os.popen('date').read().strip()}"
    send_telegram_message(msg)


def notify_error(stage: str, error: str):
    """Notify that the pipeline encountered a critical error."""
    msg = (
        f"<b>❌ ArxivIntel: Pipeline Error</b>\n\n"
        f"<b>Stage:</b> {stage}\n"
        f"<b>Error:</b> <code>{error}</code>\n\n"
        f"🕒 {os.popen('date').read().strip()}"
    )
    send_telegram_message(msg)


if __name__ == "__main__":
    # Quick test if run directly
    print("Testing Telegram Notification...")
    if notify_success("Test Topic", "manual_test", "test_id_123"):
        print("Success notification sent!")
    else:
        print("Failed to send notification. Check your .env (TELEGRAM_BOT_TOKEN/CHAT_ID).")
