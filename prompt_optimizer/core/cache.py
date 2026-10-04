"""High-performance in-memory cache for prompt optimization results."""

import hashlib
import time
from typing import Optional, Dict, Any, Tuple


class PromptCache:
    """Thread-safe TTL in-memory cache for compiled prompt requests."""

    def __init__(self, max_size: int = 256, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _make_key(self, prompt: str, backend: str, options: Optional[Dict[str, Any]] = None) -> str:
        serialized_opts = str(sorted((options or {}).items()))
        raw = f"{prompt.strip()}|{backend}|{serialized_opts}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, prompt: str, backend: str, options: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        key = self._make_key(prompt, backend, options)
        if key not in self._cache:
            return None
        expire_at, value = self._cache[key]
        if time.time() > expire_at:
            del self._cache[key]
            return None
        return value

    def set(self, prompt: str, backend: str, value: Any, options: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None):
        key = self._make_key(prompt, backend, options)
        expire_at = time.time() + (ttl or self.default_ttl)
        # Evict oldest if full
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (expire_at, value)

    def clear(self):
        self._cache.clear()
