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
        """Generate 5 random timestamps for today within the target windows."""
        plan = []
        today_str = self._get_today_str()
        
        for start_str, end_str in self.WINDOWS:
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))
            
            # Convert to minutes from midnight
            start_min = start_h * 60 + start_m
            end_min = end_h * 60 + end_m
            
            # Pick a random minute
            picked_min = random.randint(start_min, end_min)
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

    def _run_pipeline(self):
        """Invoke the main pipeline command as a subprocess."""
        print(f"🚀 [SCHEDULER] Triggering Pipeline Run: {datetime.now().isoformat()}")
        try:
            # We use subprocess to run main.py --tech-sora-post
            # This ensures clean environment and avoids import recursion issues
            cmd = [os.sys.executable, str(self.root / "main.py"), "--tech-sora-post"]
            # Set DRY_RUN_PUBLISH=0 for live posting if needed, but we respect env
            subprocess.run(cmd, cwd=str(self.root), check=True)
            print("✅ [SCHEDULER] Pipeline run completed successfully.")
        except Exception as e:
            print(f"❌ [SCHEDULER] Pipeline run failed: {e}")

    def run_forever(self):
        """Main execution loop."""
        print("🤖 ArxivIntel Smart Scheduler Started (5 Posts/Day, Peak Windows)")
        
        while True:
            plan = self.get_or_create_plan()
            now = datetime.now()
            today_str = self._get_today_str()
            
            # Find next unscheduled slot
            next_slot = None
            for slot_iso in plan["slots"]:
                slot_dt = datetime.fromisoformat(slot_iso)
                if slot_iso not in plan["completed"] and slot_dt > now:
                    next_slot = slot_iso
                    break
            
            if next_slot:
                wait_sec = (datetime.fromisoformat(next_slot) - now).total_seconds()
                print(f"  ⏭ Next post scheduled for: {next_slot} (In {wait_sec/60:.1f} minutes)")
                
                # Sleep in increments of 60s to remain responsive
                while datetime.now() < datetime.fromisoformat(next_slot):
                    time.sleep(10)
                
                # Trigger!
                self._run_pipeline()
                
                # Mark as completed
                plan["completed"].append(next_slot)
                self.plan_path.write_text(json.dumps(plan, indent=2))
            else:
                # No more slots today or early start
                print(f"  😴 No remaining slots for {today_str}. Sleeping until tomorrow...")
                time.sleep(300) # Check every 5 mins
