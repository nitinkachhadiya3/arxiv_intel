"""Pytest bootstrap: recovered-bytecode `src.utils` modules and repo root on path."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import _PycRecoveryFinder  # noqa: E402

sys.meta_path.insert(0, _PycRecoveryFinder(ROOT))
