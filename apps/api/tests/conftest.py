"""Pytest process defaults for hermetic API tests."""

import os

# Keep bare `uv run pytest` independent from local Docker. Explicit CI or local
# env vars still win, so Compose-backed runs can exercise Redis storage.
os.environ.setdefault("RATE_LIMIT_STORAGE_URL", "memory://")
