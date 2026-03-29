import os
import logging
from telegram.ext import ApplicationBuilder
from src.bot.config import Config
from src.bot.commands import register_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # 1. Load and validate config
    try:
        Config.validate()
    except EnvironmentError as e:
        logger.error(f"Configuration error: {e}")
        return

    # 2. Build the application
    token = Config.TELEGRAM_BOT_TOKEN
    app = ApplicationBuilder().token(token).build()

    # 3. Register command and message handlers
    register_handlers(app)

    # 4. Start the bot
    mode = Config.BOT_MODE.lower()
    
    if mode == "webhook":
        webhook_url = Config.WEBHOOK_URL
        if not webhook_url:
            logger.error("BOT_MODE is set to 'webhook' but WEBHOOK_URL is missing.")
            return
        
        logger.info(f"Starting bot in WEBHOOK mode at {webhook_url}")
        # In a real deployment, you'd specify listen address and port here
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", 8443)),
            url_path=token,
            webhook_url=f"{webhook_url}/{token}"
        )
    else:
        logger.info("Starting bot in POLLING mode...")
        app.run_polling()

if __name__ == "__main__":
    main()
