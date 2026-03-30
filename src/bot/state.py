import json
import os
import threading
from pathlib import Path

class PersistentState:
    """Thread-safe, file-backed dictionary for bot state persistence."""
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.lock = threading.Lock()
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
                        # Merge to ensure keys exist
                        self._data["previews"].update(loaded.get("previews", {}))
                        self._data["custom"].update(loaded.get("custom", {}))
            except Exception as e:
                print(f"⚠ Failed to load bot state: {e}")

    def _save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"⚠ Failed to save bot state: {e}")

    def __getitem__(self, key):
        with self.lock:
            return self._data[key]

    def __setitem__(self, key, value):
        with self.lock:
            self._data[key] = value
            self._save()

    def get(self, key, default=None):
        with self.lock:
            return self._data.get(key, default)

    def update_child(self, parent_key: str, child_key: str, value: any):
        """Helper to update a nested key and save immediately."""
        with self.lock:
            if parent_key not in self._data:
                self._data[parent_key] = {}
            self._data[parent_key][child_key] = value
            self._save()

# Initialize the global state with a persistent file
_ROOT = Path(__file__).resolve().parent.parent.parent
_STATE_PATH = _ROOT / "data" / "processed" / "bot_state.json"
state = PersistentState(str(_STATE_PATH))
