import logging
import sys
import json
from datetime import datetime, timezone

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Standard formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_stage(logger, stage, message, extra=None):
    """Log a structured stage event."""
    ts = datetime.now(timezone.utc).isoformat()
    log_data = {
        "ts": ts,
        "level": "INFO",
        "logger": logger.name,
        "message": message,
        "stage": stage,
    }
    if extra:
        log_data["extra"] = extra
    
    # We also print the raw JSON for the system to parse
    print(json.dumps(log_data))
    logger.info(f"[{stage}] {message}")
