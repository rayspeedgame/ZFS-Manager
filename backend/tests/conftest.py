from __future__ import annotations

import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Tests always use fixture mode so local SSH credentials do not affect results.
os.environ["ZFS_MANAGER_POLLER_MODE"] = "fixture"
os.environ["ZFS_MANAGER_POLLER_FALLBACK"] = "true"
