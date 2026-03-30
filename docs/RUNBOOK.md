# Social Agent Runbook

This document explains the full technical flow: how content is ingested, rendered, published, scheduled, and safely operated. It has been updated to reflect the new primary operational interface: **The Autonomous Telegram Bot**.

## 1) System Overview

The pipeline has these major stages:

1. **Content generation via Telegram Bot OR Scheduler**:
   - *Via Bot*: User triggers 'Get Posts' (pulls RSS/HF) or 'Custom Post' (user provides image & text).
   - *Via Scheduler*: Automated background cron job.
2. **Story planning** via strategist (`src/content/story_brief.py`) to choose single/carousel, hooks, and slide plan.
3. **Image rendering** via Gemini backgrounds + Pillow compositor (`src/media/gemini_carousel_images.py`).
4. **Publishing** to Instagram via `src/publish/instagram_publisher`.

Entrypoint for operations is typically the Telegram Bot (`src.bot.telegram_bot`).

## 2) Branch / Release Policy

- Day-to-day work: **`dev`** branch.
- Promote to production: merge/sync to **`main`** only with explicit approval.
- Current team preference in this repo: continue feature work on **`features`**.

## 3) Required Runtime Inputs

### 3.1 Environment (`.env`)

Typical required values for the Bot & Sub-processors:

- `GEMINI_API_KEY` for image + strategist generation.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
- `CLOUDINARY_KEY`, `CLOUDINARY_SECRET`, `CLOUDINARY_CLOUD_NAME` for draft caching on the web.
- Instagram/Meta credentials used by publisher (app/user/page tokens as configured in your bytecode publisher module).
- `CUSTOM_POST_DRAFT_COUNT=1` (Recommended for speed).

### 3.2 Config (`config/settings.yaml`)

Contains RSS feeds, trusted domains, scoring weights, and scheduler cadence.

## 4) Commands You Will Use
Run from repo root: `/Users/nitinkaachhadiya/social_agent`

### 4.1 Running the Interactive Telegram Bot (Recommended)
This starts the polling event loop for manual draft review, generation, and safe publishing.
```bash
source .venv/bin/activate
python -m src.bot.telegram_bot
```

### 4.2 Start Production Autopilot
```bash
./start_production.sh
```

### 4.3 CLI Overrides (Advanced)
Publish latest post JSON manually:
```bash
python main.py --post-instagram
```

## 5) End-to-End Operational Flow

For each **Custom Post** on Telegram:
1. User provides Text & Up to 5 Images.
2. State is saved using an internally re-entrant lock (thread-safe RLock).
3. The generation pipeline is spun up in an `asyncio.to_thread` executor (preventing bot hangs).
4. `generate_custom_previews` invokes Gemini Multimodal to create headlines and visual hooks.
5. Pillow composites text overlay, branding, and visuals.
6. Images are uploaded to Cloudinary, and URIs are sent back to the Telegram User.
7. Upon clicking `🚀 Post to IG`, the bot publishes directly to Meta via Graph API with natural simulated jitter.

## 6) Troubleshooting

### Error: Bot is "unresponsive" when generating Custom Posts
The generation is running in an async executor thread. Depending on Gemini's load and the slide count, this can take 1-3 minutes. Monitor the stdout terminal for HTTP request logs.

### Error: Deadlock during session update
If you see the bot hang immediately upon interaction, verify that `src/bot/state.py` has initialized `threading.RLock()` instead of `threading.Lock()`.

### Error: Exception "No module named X"
Ensure you install all bot requirements:
```bash
pip install python-telegram-bot python-dotenv cloudinary httpx
```
