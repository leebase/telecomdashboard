"""TTL-aware caching system for metadata data provider."""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""
    data: pd.DataFrame
    timestamp: float
    ttl_seconds: int
    key: str

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.timestamp > self.ttl_seconds


class TTLCache:
    """TTL-aware cache with optional SQLite persistence."""

    def __init__(
        self,
        default_ttl: int = 300,
        max_size: int = 100,
        sqlite_path: Optional[Path] = None,
    ):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.sqlite_path = sqlite_path
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._sqlite_conn: Optional[sqlite3.Connection] = None

        if sqlite_path:
            self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite cache table."""
        if not self.sqlite_path:
            return

        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._sqlite_conn = sqlite3.connect(str(self.sqlite_path))

        with self._sqlite_conn:
            self._sqlite_conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    data BLOB,
                    timestamp REAL,
                    ttl_seconds INTEGER
                )
            """)

        # Load existing entries
        self._load_from_sqlite()

    def _load_from_sqlite(self) -> None:
        """Load valid entries from SQLite."""
        if not self._sqlite_conn:
            return

        with self._sqlite_conn:
            cursor = self._sqlite_conn.execute(
                "SELECT key, data, timestamp, ttl_seconds FROM cache"
            )
            for row in cursor:
                key, data_blob, timestamp, ttl_seconds = row
                if time.time() - timestamp <= ttl_seconds:
                    try:
                        # Deserialize DataFrame (simplified - in practice use pickle or similar)
                        data = pd.read_pickle(data_blob) if data_blob else pd.DataFrame()
                        entry = CacheEntry(data, timestamp, ttl_seconds, key)
                        self._cache[key] = entry
                    except Exception as e:
                        logger.warning(f"Failed to load cache entry {key}: {e}")

    def _save_to_sqlite(self, entry: CacheEntry) -> None:
        """Save entry to SQLite."""
        if not self._sqlite_conn:
            return

        try:
            # Serialize DataFrame (simplified)
            data_blob = entry.data.to_pickle() if not entry.data.empty else None
            with self._sqlite_conn:
                self._sqlite_conn.execute(
                    "INSERT OR REPLACE INTO cache (key, data, timestamp, ttl_seconds) VALUES (?, ?, ?, ?)",
                    (entry.key, data_blob, entry.timestamp, entry.ttl_seconds)
                )
        except Exception as e:
            logger.warning(f"Failed to save cache entry {entry.key}: {e}")

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Get cached data if valid."""
        with self._lock:
            self._cleanup_expired()
            entry = self._cache.get(key)
            if entry and not entry.is_expired:
                logger.debug(f"Cache hit for {key}")
                return entry.data
            elif entry:
                logger.debug(f"Cache expired for {key}")
                self._cache.pop(key, None)
            return None

    def put(self, key: str, data: pd.DataFrame, ttl_seconds: Optional[int] = None) -> None:
        """Store data in cache."""
        with self._lock:
            self._cleanup_expired()
            ttl = ttl_seconds or self.default_ttl
            entry = CacheEntry(data, time.time(), ttl, key)

            # Evict if at capacity (LRU-like)
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
                self._cache.pop(oldest_key, None)

            self._cache[key] = entry
            self._save_to_sqlite(entry)
            logger.debug(f"Cached {key} with TTL {ttl}s")

    def invalidate(self, key: str) -> bool:
        """Remove specific entry."""
        with self._lock:
            if key in self._cache:
                self._cache.pop(key, None)
                if self._sqlite_conn:
                    with self._sqlite_conn:
                        self._sqlite_conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                logger.debug(f"Invalidated cache for {key}")
                return True
            return False

    def clear(self) -> int:
        """Clear all entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            if self._sqlite_conn:
                with self._sqlite_conn:
                    self._sqlite_conn.execute("DELETE FROM cache")
            logger.info(f"Cleared {count} cache entries")
            return count

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self._cleanup_expired()
            total = len(self._cache)
            expired = sum(1 for entry in self._cache.values() if entry.is_expired)
            return {
                "total_entries": total,
                "expired_entries": expired,
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "sqlite_enabled": self.sqlite_path is not None,
            }

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            self._cache.pop(key, None)
            if self._sqlite_conn:
                with self._sqlite_conn:
                    self._sqlite_conn.execute("DELETE FROM cache WHERE key = ?", (key,))

    def __del__(self) -> None:
        """Cleanup SQLite connection."""
        if self._sqlite_conn:
            self._sqlite_conn.close()


# Global cache instance
_cache_instance: Optional[TTLCache] = None
_cache_lock = threading.Lock()


def get_cache(
    default_ttl: int = 300,
    max_size: int = 100,
    sqlite_path: Optional[Path] = None,
) -> TTLCache:
    """Get or create global cache instance."""
    global _cache_instance
    with _cache_lock:
        if _cache_instance is None:
            _cache_instance = TTLCache(default_ttl, max_size, sqlite_path)
        return _cache_instance


__all__ = ["TTLCache", "get_cache"]