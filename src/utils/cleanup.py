"""
Disk Cleanup — Purges old rendering artifacts to save space.
Removes folders in output/images/ older than X days.
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path


def purge_old_artifacts(days: int = 7, dry_run: bool = False):
    """Delete output/images/ folders older than 'days'."""
    root = Path(__file__).resolve().parent.parent.parent
    target_dir = root / "output" / "images"
    
    if not target_dir.exists():
        return

    now = time.time()
    cutoff = now - (days * 86400)
    
    print(f"🧹 Running Disk Cleanup (Threshold: {days} days)...")
    
    purged_count = 0
    for item in target_dir.iterdir():
        if item.is_dir() and item.name.startswith(("render_", "cli_instagram_test_")):
            # Check modification time
            mtime = item.stat().st_mtime
            if mtime < cutoff:
                if dry_run:
                    print(f"  [DRY RUN] Would delete: {item.name} (Modified: {time.ctime(mtime)})")
                else:
                    try:
                        shutil.rmtree(item)
                        print(f"  🗑 Deleted: {item.name}")
                        purged_count += 1
                    except Exception as e:
                        print(f"  ⚠ Failed to delete {item.name}: {e}")
    
    print(f"✅ Cleanup finished. Purged {purged_count} directories.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    purge_old_artifacts(days=args.days, dry_run=args.dry_run)
