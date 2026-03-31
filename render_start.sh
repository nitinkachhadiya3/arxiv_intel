#!/bin/bash

# Pre-start: Sync Environment
export PYTHONPATH=$PWD
echo "🚀 Starting ArxivIntel Unified Deployment (Scheduler + Bot)..."

# 1. Start the Smart Scheduler in the background
# It generates plans and runs the main pipeline loop.
python3 -m src.scheduler.scheduler &
SCHEDULER_PID=$!
echo "📝 Scheduler started (PID: $SCHEDULER_PID)"

# 2. Start the Telegram Bot in the foreground
# On Render Free Tier, the bot will use Webhook mode to bind to $PORT
echo "🤖 Starting Telegram Bot..."
python3 -m src.bot.telegram_bot

# Cleanup: if the bot dies, kill the scheduler too
echo "🛑 Bot stopped. Cleaning up scheduler (PID: $SCHEDULER_PID)..."
kill $SCHEDULER_PID
