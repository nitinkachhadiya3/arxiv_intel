import json
import os
import threading
from pathlib import Path

class PersistentState:
    """Thread-safe, file-backed dictionary for bot state persistence."""
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.lock = threading.RLock()
        self._data = {
            "previews": {},  # uuid -> preview dict
            "custom": {},    # uuid -> custom draft dict
        }
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        with self.lock:
                            self._data.update(loaded)
                            # Ensure required keys exist
                            if "previews" not in self._data: self._data["previews"] = {}
                            if "custom" not in self._data: self._data["custom"] = {}
            except Exception as e:
                print(f"⚠ Failed to load bot state: {e}")

    def _save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                with self.lock:
                    json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"⚠ Failed to save bot state: {e}")

    def get_user_data(self, chat_id: int) -> dict:
        """Get session data for a specific user, or a new session if not present."""
        str_id = str(chat_id)
        with self.lock:
            if str_id not in self._data:
                self._data[str_id] = {"mode": "idle", "desc": "", "photos": []}
            return self._data[str_id].copy()

    def set_user_data(self, chat_id: int, data: dict):
        """Update session data for a specific user and save immediately."""
        str_id = str(chat_id)
        with self.lock:
            self._data[str_id] = data
            self._save()

    def update_child(self, parent_key: str, child_key: str, child_val: dict):
        """Update a specific child dictionary and save immediately."""
        with self.lock:
            if parent_key not in self._data:
                self._data[parent_key] = {}
            self._data[parent_key][child_key] = child_val
            self._save()

    def get(self, key: str, default=None):
        with self.lock:
            return self._data.get(key, default)

    def __getitem__(self, key: str):
        with self.lock:
            return self._data[key]


# Initialize the global state with a persistent file
_ROOT = Path(__file__).resolve().parent.parent.parent
_STATE_PATH = _ROOT / "data" / "processed" / "bot_state.json"
state = PersistentState(str(_STATE_PATH))
