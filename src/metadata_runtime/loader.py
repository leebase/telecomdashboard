"""Metadata configuration loader with on-disk caching."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import MetadataConfig


@dataclass
class MetadataCacheEntry:
    path: Path
    mtime_ns: int
    config: MetadataConfig


_cache_lock = Lock()
_cache: dict[Path, MetadataCacheEntry] = {}


class MetadataLoadError(RuntimeError):
    """Raised when metadata parsing or validation fails."""

    def __init__(self, message: str, *, errors: Optional[list[dict]] = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_metadata(path: Path | str, *, force_reload: bool = False) -> MetadataConfig:
    """Load metadata from disk with basic caching.

    Args:
        path: Path to the metadata YAML file.
        force_reload: Ignore the cached entry even if unchanged.

    Returns:
        Parsed :class:`MetadataConfig` instance.
    """

    path_obj = Path(path).expanduser().resolve()
    if not path_obj.exists():
        raise FileNotFoundError(path_obj)

    stat = path_obj.stat()
    mtime_ns = stat.st_mtime_ns

    with _cache_lock:
        entry = _cache.get(path_obj)
        if entry and not force_reload and entry.mtime_ns == mtime_ns:
            return entry.config

    payload = _load_yaml(path_obj)

    try:
        config = MetadataConfig.parse_obj(payload)
    except ValidationError as exc:  # pragma: no cover - re-raised with context
        raise MetadataLoadError(
            "Metadata validation failed", errors=exc.errors()
        ) from exc

    with _cache_lock:
        _cache[path_obj] = MetadataCacheEntry(path=path_obj, mtime_ns=mtime_ns, config=config)

    return config


def validate_metadata(path: Path | str) -> MetadataConfig:
    """Validate metadata file and return the parsed configuration."""
    try:
        return load_metadata(path, force_reload=True)
    except (FileNotFoundError, MetadataLoadError) as exc:
        raise exc


def clear_cache(path: Optional[Path | str] = None) -> None:
    """Invalidate cached metadata."""
    with _cache_lock:
        if path is None:
            _cache.clear()
        else:
            _cache.pop(Path(path).expanduser().resolve(), None)
