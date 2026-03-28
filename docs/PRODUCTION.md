# ArxivIntel: Final Production Go-Live Guide

Follow these steps to transition your Instagram content pipeline from development to full autonomous production.

## 1. Environment Configuration

Ensure your `.env` file contains the following (especially the new alerting keys):

```bash
# 🤖 Instagram / Meta Credentials
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
INSTAGRAM_ACCESS_TOKEN=...

# 🖼 Image Generation
GEMINI_API_KEY=...

# 📱 Production Monitoring (New)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# ⚙️ Operational Flags
DRY_RUN_PUBLISH=0         # Set to 0 for LIVE posting
ALLOW_REPEAT_POST=0       # Prevents duplicate topics
```

---

## 2. Launching the System

### **Option A: The Simple Production Script (Recommended)**
This script keeps the scheduler alive even if it crashes or the server restarts.

```bash
chmod +x start_production.sh
./start_production.sh
```

### **Option B: Using PM2 (Professional)**
If you have `pm2` installed on your server, use this for better background management:

```bash
pm2 start start_production.sh --name "arxiv-intel-scheduler"
pm2 save
```

---

## 3. How the Automation Works

### **📅 Smart Scheduling**
- The system runs **5 times a day** during peak India/US hours.
- **Double Randomness**: Every day, the windows shift by a random "Daily Drift" and then pick a random minute within that shift. This makes your account look human.

### **🧽 Automatic Maintenance**
- **Artifact Cleanup**: At 00:00 every night, the system automatically deletes `output/images/` folders older than **7 days** to save disk space.

### **🔔 Instant Alerts**
- You will receive a **Telegram notification** on your phone immediately after each post is published (or if an error occurs).

---

## 4. Monitoring & Troubleshooting

- **Check Logs**: `tail -f output.log` (if using redirection) or `pm2 logs`.
- **Verify Plan**: Check `output/scheduler_plan.json` to see when the next 5 posts are scheduled.
- **Test Alert**: Run `python src/utils/notifier.py --test` to ensure your phone receives the ping.

---

**You are now ready for 24/7 autonomous operation!** 🚀
