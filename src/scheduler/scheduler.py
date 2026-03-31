"""
Smart Scheduler — source-based replacement for bytecode.
Generates randomized daily plans for 5 posts per day targeting peak India/US hours.
"""
from __future__ import annotations

import json
import os
import random
import time
import subprocess
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from typing import Any, Dict, List, Optional


class JobScheduler:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.root = Path(__file__).resolve().parent.parent.parent
        self.plan_path = self.root / "output" / "scheduler_plan.json"
        
        # Load windows from config or use defaults
        sched_cfg = getattr(config, "scheduler", {})
        if isinstance(sched_cfg, dict):
            self.windows = sched_cfg.get("peak_windows_ist", self.DEFAULT_WINDOWS)
        else:
            self.windows = self.DEFAULT_WINDOWS

    # IST Windows (expressed as HH:MM start/end) - Defaults if not in config
    DEFAULT_WINDOWS = [
        ("08:30", "10:30"), # India Morning / US Night
        ("13:00", "15:00"), # India Afternoon
        ("18:30", "20:30"), # India Evening / US Morning
        ("21:15", "23:15"), # India Night
        ("05:45", "07:45"), # US Evening / India Early Morning
    ]

    def _get_today_str(self) -> str:

        return datetime.now().strftime("%Y-%m-%d")

    def generate_daily_plan(self) -> List[str]:
        """
        Generate 5 random timestamps for today with 'Double Randomness':
        1. A daily 'Global Drift' that shifts all windows.
        2. A random slot within each shifted window.
        """
        plan = []
        today_str = self._get_today_str()
        
        # 1. Global daily drift (e.g., +/- 20 minutes) to shift all windows
        global_drift = random.randint(-20, 20)
        print(f"  🎲 [SCHEDULER] Daily drift calculated: {global_drift:+} minutes")

        for start_str, end_str in self.windows:
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))
            
            # Convert to minutes from midnight and apply global drift
            start_min = (start_h * 60 + start_m) + global_drift
            end_min = (end_h * 60 + end_m) + global_drift
            
            # 2. Pick a random minute within the shifted window
            picked_min = random.randint(start_min, end_min)
            
            # Ensure we don't bleed into the next/previous day in a weird way
            picked_min = max(0, min(picked_min, 1439))
            
            h, m = divmod(picked_min, 60)
            
            # Format as ISO timestamp for today
            dt = datetime.strptime(f"{today_str} {h:02d}:{m:02d}", "%Y-%m-%d %H:%M")
            plan.append(dt.isoformat())
            
        plan.sort()
        return plan


    def get_or_create_plan(self) -> Dict[str, Any]:
        """Load today's plan or create a new one."""
        today = self._get_today_str()
        if self.plan_path.exists():
            try:
                data = json.loads(self.plan_path.read_text())
                if data.get("date") == today:
                    return data
            except:
                pass
        
        # Create new plan
        new_plan = {
            "date": today,
            "slots": self.generate_daily_plan(),
            "completed": []
        }
        self.plan_path.parent.mkdir(parents=True, exist_ok=True)
        self.plan_path.write_text(json.dumps(new_plan, indent=2))
        return new_plan

    def _run_pipeline(self, topic_info: Optional[Dict[str, Any]] = None):
        """Invoke the main pipeline command and notify on success/failure."""
        from src.utils.notifier import notify_success, notify_error
        
        topic_name = topic_info.get("topic", "Unknown Topic") if topic_info else "Scheduled Post"
        source_name = topic_info.get("content_source", "unknown") if topic_info else "rotation"

        print(f"🚀 [SCHEDULER] Triggering Pipeline Run: {datetime.now().isoformat()}")
        try:
            cmd = [os.sys.executable, str(self.root / "main.py"), "--tech-sora-post"]
            result = subprocess.run(cmd, cwd=str(self.root), capture_output=True, text=True, check=True)
            
            # Simple success detection from output (or just success exit code)
            print("✅ [SCHEDULER] Pipeline run completed successfully.")
            notify_success(topic_name, source_name)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with exit code {e.returncode}: {e.stderr[:200]}"
            print(f"❌ [SCHEDULER] Pipeline run failed: {error_msg}")
            notify_error("Main Pipeline", error_msg)
        except Exception as e:
            print(f"❌ [SCHEDULER] Unexpected error: {e}")
            notify_error("Scheduler Execution", str(e))

    def run_forever(self):
        """Main execution loop with daily cleanup trigger."""
        from src.utils.cleanup import purge_old_artifacts
        
        print("🤖 ArxivIntel Smart Scheduler Started (5 Posts/Day, Peak Windows)")
        
        last_cleanup_date = None

        while True:
            plan = self.get_or_create_plan()
            now = datetime.now()
            today_str = self._get_today_str()
            
            # 1. Run Daily Cleanup at 00:00 IST (roughly)
            if today_str != last_cleanup_date:
                purge_old_artifacts(days=7)
                last_cleanup_date = today_str

            # 2. Find next unscheduled slot
            next_slot = None
            slot_info = None
            for slot_iso in plan["slots"]:
                if slot_iso not in plan["completed"]:
                    slot_dt = datetime.fromisoformat(slot_iso)
                    if slot_dt > now:
                        next_slot = slot_iso
                        break
            
            if next_slot:
                wait_sec = (datetime.fromisoformat(next_slot) - now).total_seconds()
                print(f"  ⏭ Next post scheduled for: {next_slot} (In {wait_sec/60:.1f} minutes)")
                
                while datetime.now() < datetime.fromisoformat(next_slot):
                    time.sleep(10)
                
                # Fetch a quick topic preview if possible for notification context
                # (This is optional; _run_pipeline will also re-discover topic anyway)
                self._run_pipeline()
                
                # Mark as completed
                plan["completed"].append(next_slot)
                self.plan_path.write_text(json.dumps(plan, indent=2))
            else:
                print(f"  😴 No remaining slots for {today_str}. Sleeping until tomorrow...")
                time.sleep(300)

if __name__ == "__main__":
    from src.bot.config import Config
    try:
        Config.validate()
        scheduler = JobScheduler(Config)
        scheduler.run_forever()
    except Exception as e:
        print(f"❌ Scheduler startup failed: {e}")
