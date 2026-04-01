# ArxivIntel Telegram Bot

## Prerequisites

1. Python 3.10+
2. A `.env` file containing the required configurations. 

## Environment Setup (.env)

The bot relies on a `.env` file for all configurations. Below is the comprehensive list of required and optional parameters:

| Category | Variable | Description | Default |
| --- | --- | --- | --- |
| **Core AI** | `GEMINI_API_KEY` | Google Gemini API Key (Required) | - |
| | `GEMINI_IMAGE_MODEL` | Gemini Image Model (e.g. `gemini-2.0-flash-exp`) | `gemini-2.0-flash-exp` |
| | `GEMINI_IMAGE_ASPECT_RATIO` | Generation aspect ratio (`3:4`, `1:1`, `9:16`) | `3:4` |
| **Telegram** | `TELEGRAM_BOT_TOKEN` | Bot API Token from @BotFather (Required) | - |
| | `TELEGRAM_CHAT_ID` | Main chat ID for auto-posting | - |
| | `BOT_MODE` | `polling` (dev) or `webhook` (production) | `polling` |
| | `WEBHOOK_URL` | App URL for webhook mode | - |
| **Cloudinary** | `CLOUDINARY_CLOUD_NAME`| Cloudinary Cloud Name (Required) | - |
| | `CLOUDINARY_KEY` | Cloudinary API Key | - |
| | `CLOUDINARY_SECRET` | Cloudinary API Secret | - |
| **Instagram** | `INSTAGRAM_ACCESS_TOKEN`| Long-lived access token for Meta API | - |
| | `INSTAGRAM_BUSINESS_ACCOUNT_ID`| Instagram Business Account ID | - |
| **Strategy** | `IMAGE_RENDER_MODE` | `cinematic_overlay` (Modern) or `arxiv_integrated` (3D) | `cinematic_overlay` |
| | `BRAND_NAME` | Global brand label on slides | `ArXiv Intel` |
| | `CONTENT_CATEGORY` | Primary vertical (e.g. `technology`, `ipl`) | `technology` |
| | `PROFILE_LOGO_MODE` | `mark` (Subtle) or `tree` (Bold) | `mark` |
| | `STORY_MAX_SLIDES` | Max slides per carousel | `6` |
| | `CUSTOM_POST_DRAFT_COUNT`| Number of drafts to generate for custom prompts | `2` |

## Installation

Activate your virtual environment and install the dependencies:

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Bot

To start the bot in the background or during active development, you can run the Telegram bot module directly:

```bash
source .venv/bin/activate
python -m src.bot.telegram_bot
```

## Production Start

For automated environments that need a smart scheduler process, you can use the production script:

```bash
./start_production.sh
```

---

## 🚀 Deployment on Render (Free Tier)

This repository is optimized for deployment on **Render's Free Web Service**.

### 1. Environment Variable Configuration
Set the following variables in your Render Dashboard:

| Variable | Description | Value |
| --- | --- | --- |
| `GEMINI_API_KEY` | Your Google Gemini API Key | `AIza...` |
| `TELEGRAM_BOT_TOKEN` | Your Telegram Bot Token | `12345:ABC...` |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary Name | `dsoq...` |
| `CLOUDINARY_KEY` | Cloudinary API Key | `...` |
| `CLOUDINARY_SECRET` | Cloudinary API Secret | `...` |
| `BOT_MODE` | Bot Mode | `webhook` |
| `WEBHOOK_URL` | Your App URL | `https://your-app-name.onrender.com` |

### 2. Render Deployment Settings
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `chmod +x render_start.sh && ./render_start.sh`

> [!TIP]
> **Free Tier Hibernate**: Render Free Tier Web Services sleep after 15 minutes of inactivity. The first time you message the bot after a long break, it may take ~30 seconds to wake up and respond.

