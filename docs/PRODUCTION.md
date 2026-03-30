# ArxivIntel: Final Production Go-Live Guide

Follow these steps to transition your Instagram content pipeline from development to full autonomous production, and keep the interactive Telegram companion bot alive 24/7.

## 1. Environment Configuration

Ensure your `.env` file contains the following:

```bash
# 🤖 Instagram / Meta Credentials
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
INSTAGRAM_ACCESS_TOKEN=...

# 🖼 Image Generation & Cloudinary Drafts
GEMINI_API_KEY=...
CLOUDINARY_KEY=...
CLOUDINARY_SECRET=...
CLOUDINARY_CLOUD_NAME=...

# 📱 Telegram Bot Configurations
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
BOT_MODE=polling  # or webhook

# ⚙️ Operational Flags
DRY_RUN_PUBLISH=0         # Set to 0 for LIVE posting
ALLOW_REPEAT_POST=0       # Prevents duplicate topics
CUSTOM_POST_DRAFT_COUNT=1 # Recommended optimized pipeline
```

---

## 2. Launching the System

You have two background processes to run:
1. **The Scheduler Autopilot** (`start_production.sh` / `main.py --run-scheduler`)
2. **The Telegram Companion Bot** (`python -m src.bot.telegram_bot`)

### Option A: Using PM2 (Highly Recommended Professional Setup)
If you have `pm2` installed on your server, you can perfectly run both background loops and have them managed simultaneously.

```bash
# Ensure dependencies are installed
source .venv/bin/activate
pip install python-telegram-bot httpx python-dotenv cloudinary

# Start Autopilot Schedule
pm2 start ./start_production.sh --name "arxivintel-scheduler"

# Start Operational Telegram Bot 
pm2 start "python -m src.bot.telegram_bot" --name "arxivintel-tg-bot"

# Save pm2 list so they survive system restarts
pm2 save
pm2 startup
```

### Option B: Tmux / Screen Setup
If you do not have PM2, you can use traditional terminal multiplexers to run them alongside each other inside `tmux` sessions.

---

## 3. How the Automation Works

### **📅 Smart Scheduling**
- The system runs **5 times a day** during peak India/US hours.
- **Double Randomness**: Every day, the windows shift by a random "Daily Drift" and then pick a random minute within that shift. This makes your account look human.

### **✨ Interactive Overrides via Telegram**
- If your 5 daily automated posts aren't enough, you can request Custom Posts to run immediately through your Telegram bot!
- The bot features an **asynchronous generation pipeline**. When you request a Draft through Telegram, it runs on an isolated thread, preventing the polling loop from lagging.

### **🧽 Automatic Maintenance**
- **Artifact Cleanup**: At 00:00 every night, the system automatically deletes `output/images/` folders older than **7 days** to save disk space.

### **🔔 Instant Alerts**
- You will receive a **Telegram notification** on your phone immediately after each post is published (or if an error occurs).

---

## 4. Monitoring & Troubleshooting

- **Check Logs**: `pm2 logs` or refer to `bot.log` in the root directory.
- **Verify Plan**: Check `output/scheduler_plan.json` to see when the next 5 posts are scheduled.
- **Deadlock Check**: The bot leverages re-entrant locks (`RLock`); ensure `state.json` inside the `data` directory maintains appropriate permissions if transferring servers.

---

**You are now equipped with 24/7 autonomous operations and a mobile Command Center!** 🚀
