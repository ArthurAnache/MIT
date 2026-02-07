"""Simple TTL cache with disk persistence for trends.

- Cache key is typically geo.
- Cache duration: 15 minutes (configurable).
- On fetch failure, caller can request last successful cached value.

This is intentionally lightweight for hackathon MVP.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    stored_at: float


class TTLCache:
    """Thread-safe TTL cache with optional JSON disk persistence."""

    def __init__(self, ttl_seconds: int, persist_path: Optional[Path] = None):
        self.ttl_seconds = ttl_seconds
        self.persist_path = persist_path
        self._lock = threading.RLock()
        self._data: Dict[str, CacheEntry] = {}
        if self.persist_path:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def get(self, key: str) -> Tuple[Optional[Any], bool]:
        """Return (value, is_fresh)."""
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None, False
            if entry.expires_at >= now:
                return entry.value, True
            # Expired but still available as stale fallback
            return entry.value, False

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        entry = CacheEntry(value=value, expires_at=now + self.ttl_seconds, stored_at=now)
        with self._lock:
            self._data[key] = entry
            self._save()

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._save()

    def _save(self) -> None:
        if not self.persist_path:
            return
        payload: Dict[str, Dict[str, Any]] = {}
        for k, v in self._data.items():
            payload[k] = {
                "value": v.value,
                "expires_at": v.expires_at,
                "stored_at": v.stored_at,
            }
        tmp = self.persist_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.persist_path)

    def _load(self) -> None:
        if not self.persist_path or not self.persist_path.exists():
            return
        try:
            payload = json.loads(self.persist_path.read_text(encoding="utf-8"))
        except Exception:
            return
        now = time.time()
        for k, d in payload.items():
            # Do not drop expired entries; they are useful for fallback behavior.
            expires_at = float(d.get("expires_at", now - 1))
            stored_at = float(d.get("stored_at", now - 1))
            self._data[k] = CacheEntry(value=d.get("value"), expires_at=expires_at, stored_at=stored_at)
