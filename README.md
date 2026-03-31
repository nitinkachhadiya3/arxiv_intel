# ArxivIntel Telegram Bot

## Prerequisites

1. Python 3.10+
2. A `.env` file containing the required configurations. 

## Environment Variables (.env)

Ensure your `.env` contains at least:
- `GEMINI_API_KEY`: API Key for Google Gemini.
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token.
- `CLOUDINARY_KEY`, `CLOUDINARY_SECRET`, `CLOUDINARY_CLOUD_NAME`: Credentials for image hosting.
- `BOT_MODE`: Typically set to `polling`.
- `CUSTOM_POST_DRAFT_COUNT`: Determines how many custom image drafts to generate (e.g., 1 or 2).

## Installation

Activate your virtual environment and install the dependencies:

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install cloudinary python-telegram-bot python-dotenv httpx
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

