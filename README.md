# ArxivIntel Telegram Bot

## Prerequisites

1. Python 3.10+
2. A `.env` file containing the required configurations. 

## Environment Setup (.env)

The bot requires a `.env` file for all configuration. Below is the exhaustive list of all variables utilized across the codebase with official setup links:

| Category | Variable | Description | Official Documentation / Setup Link |
| --- | --- | --- | --- |
| **Generative AI** | `GEMINI_API_KEY` | Google Gemini API Key | [Get API Key](https://aistudio.google.com/app/apikey) |
| | `GEMINI_MODEL` | Strategist Model name | [Model Documentation](https://ai.google.dev/gemini-api/docs/models/gemini) |
| | `GEMINI_IMAGE_MODEL` | Visual Generator name | [Image Generation Guide](https://ai.google.dev/gemini-api/docs/imagen) |
| | `GEMINI_IMAGE_ASPECT_RATIO`| Image ratio (`3:4`, `1:1`) | [Aspect Ratio Support](https://ai.google.dev/gemini-api/docs/imagen#aspect-ratio) |
| **Telegram** | `TELEGRAM_BOT_TOKEN` | Bot API Token | [@BotFather Guide](https://core.telegram.org/bots/tutorial#obtain-api-token) |
| | `TELEGRAM_CHAT_ID` | Your channel or group ID | [Get Chat ID Utility](https://t.me/getmyid_bot) |
| | `BOT_MODE` | `polling` (dev) or `webhook` | [Running Modes](https://core.telegram.org/bots/webhooks) |
| | `WEBHOOK_URL` | **Required for webhook mode** | [Webhooks Tutorial](https://core.telegram.org/bots/webhooks#setting-a-webhook) |
| | `PORT` | Webhook listener port | [Server Configuration](https://render.com/docs/deploy-python) |
| **Cloudinary** | `CLOUDINARY_CLOUD_NAME`| Cloudinary Cloud Name | [Cloudinary Dashboard](https://cloudinary.com/console) |
| | `CLOUDINARY_KEY` | Cloudinary API Key | [API Key Guide](https://cloudinary.com/documentation/cloudinary_credentials_tutorial) |
| | `CLOUDINARY_SECRET` | Cloudinary API Secret | [Security Best Practices](https://cloudinary.com/documentation/admin_api#authentication) |
| **Meta / Instagram** | `INSTAGRAM_ACCESS_TOKEN`| Long-lived system token | [Meta Getting Started](https://developers.facebook.com/docs/instagram-api/getting-started) |
| | `INSTAGRAM_BUSINESS_ACCOUNT_ID`| Instagram Business ID | [IG User Reference](https://developers.facebook.com/docs/instagram-api/reference/ig-user) |
| | `INSTAGRAM_USERNAME` | Instagram Username | [Profile Lookup](https://developers.facebook.com/docs/instagram-api/reference/ig-user) |
| | `META_APP_ID` | Meta Application ID | [App Dashboard](https://developers.facebook.com/apps/) |
| | `META_APP_SECRET` | Meta Application Secret | [App Settings](https://developers.facebook.com/apps/) |
| **Optional Social** | `FACEBOOK_PAGE_ID` | Linked FB Page ID | [FB Page Reference](https://developers.facebook.com/docs/graph-api/reference/page/) |
| | `FACEBOOK_PAGE_ACCESS_TOKEN`| Page-specific token | [Page Tokens Guide](https://developers.facebook.com/docs/pages/access-tokens) |
| | `LINKEDIN_ORGANIZATION_ID`| LinkedIn Org URN | [LinkedIn Org Lookup](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/organizations/organization-lookup-api) |
| | `X_BEARER_TOKEN` | Twitter Bearer Token | [X Dev Portal](https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api) |
| **Internal Bot** | `IMAGE_RENDER_MODE` | `cinematic_overlay` (Modern) | - |
| | `BRAND_NAME` | Global label on slides | - |
| | `CONTENT_CATEGORY` | Primary vertical (e.g. `ipl`) | - |
| | `STORY_MAX_SLIDES` | Max slides per post | - |
| | `STORY_STRATEGIST_ENABLED`| Toggle AI Strategist | - |
| | `REQUIRE_GEMINI_FOR_PUBLISH`| Validate output | - |

## Running Modes

The bot supports two operational modes controlled by the `BOT_MODE` variable:

-   **Polling (`polling`)**: Recommended for **Local Development**. The bot proactively checks for new messages. No public URL or SSL certificate is required.
-   **Webhook (`webhook`)**: Recommended for **Production** (e.g. Render, AWS). Telegram pushes messages to your `WEBHOOK_URL`. This requires a public HTTPS URL and setting the `PORT` (default `8443`).

## Installation

Activate your virtual environment and install dependencies:

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

