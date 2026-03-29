# ArxivIntel Telegram Bot

An autonomous and interactive Telegram bot to manage the ArxivIntel Instagram content pipeline.

## Features
- **Get Posts**: Fetch 5 fresh topics from rotation sources (RSS, HF, Google Trends), preview them as media groups, and publish any of them with one click.
- **Custom Post**: User can provide a description and up to 5 photos. The system uses Gemini (Multimodal) to generate a professional caption and a new image generation prompt to create high-quality editorial drafts.
- **Ghost-Safe Publishing**: All publication requests from the bot use the same jitter and safety checks as the automated scheduler.

## Configuration (.env)
Add the following to your `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
BOT_MODE=polling  # or 'webhook' for production
WEBHOOK_URL=https://your-domain.com  # only required for webhook mode
CUSTOM_POST_DRAFT_COUNT=2
```

## How to Run
### Local Development (Polling)
1. Ensure `BOT_MODE=polling` in `.env`.
2. Install dependencies: `pip install python-telegram-bot`
3. Run the bot:
   ```bash
   python -m src.bot.telegram_bot
   ```

### Production (Webhook)
1. Ensure `BOT_MODE=webhook` and `WEBHOOK_URL` is set.
2. The bot will automatically register the webhook on startup.
3. Run with a process manager like PM2 or Docker.

## Flow Diagram
```mermaid
graph TD
    A[User /start] --> B{Choose Action}
    B -->|Get Posts| C[Fetch 5 topics]
    C --> D[Preview Media Group]
    D --> E[Post to IG Button]
    
    B -->|Custom Post| F[Collect Description]
    F --> G[Collect Up to 5 Photos]
    G --> H[Gemini LLM Generation]
    H --> I[Generate 2 Drafts]
    I --> J[Preview Drafts]
    J --> K[Post to IG Button]
    
    E --> L[Instagram Publisher]
    K --> L
    L --> M[Success Notification]
```
