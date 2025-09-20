"""Feature flag helpers for toggling the metadata runtime."""
from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def is_metadata_enabled() -> bool:
    value = os.getenv("USE_METADATA", "false")
    return value.strip().lower() in {"1", "true", "yes", "on"}


__all__ = ["is_metadata_enabled"]
