#!/bin/bash
# ArxivIntel Production Launcher
# Keeps the smart scheduler alive even if it crashes.

# Ensure we are in the right directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "🚀 [PRODUCTION] Starting ArxivIntel Smart Scheduler..."
echo "🕒 Current Time: $(date)"

while true; do
  # Run the scheduler
  python main.py --run-scheduler
  
  # If it exits, wait 10 seconds and restart
  echo "⚠️ [PRODUCTION] Scheduler stopped or crashed. Restarting in 10s..."
  sleep 10
done
