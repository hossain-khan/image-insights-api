"""In-memory LRU cache for image analysis results.

Privacy-First Design:
- Cache keys are BLAKE2b hashes of image content + request parameters.
  The original image bytes, URLs, and filenames are NEVER stored.
- Cache values contain only aggregate metrics (no pixel data or PII).
- Cache entries expire after a configurable TTL to bound memory usage.
- LRU eviction ensures the cache never exceeds a configurable maximum size.
"""

import copy
import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)


def compute_cache_key(image_bytes: bytes, metrics: set[str], edge_mode: str | None) -> str:
    """
    Compute a compact, privacy-safe cache key for an image analysis request.

    The key is a BLAKE2b digest of the image content combined with the
    requested metrics and edge mode.  The original image bytes and any
    URL or filename are discarded – only the hash is kept.

    BLAKE2b is used instead of SHA-256 because it is significantly faster
    on modern hardware while still providing strong collision resistance for
    cache correctness.

    Args:
        image_bytes: Raw image content used solely to compute the hash.
        metrics: Set of requested metric names (e.g. {"brightness", "median"}).
        edge_mode: Optional edge analysis mode string.

    Returns:
        A hex-encoded BLAKE2b digest string.
    """
    hasher = hashlib.blake2b()
    hasher.update(image_bytes)
    # Use "|" as separator between components to prevent hash collisions
    # (e.g. metrics="" + edge_mode="all" vs metrics="all" + edge_mode="")
    hasher.update(b"|")
    hasher.update(",".join(sorted(metrics)).encode())
    hasher.update(b"|")
    hasher.update((edge_mode or "").encode())
    return hasher.hexdigest()


class ImageAnalysisCache:
    """
    Thread-safe in-memory LRU cache with TTL for image analysis results.

    Stores only aggregate metric dictionaries – never image bytes, URLs,
    or any personally identifiable information.
    """

    def __init__(self, max_size: int = 128, ttl_seconds: int = 3600) -> None:
        """
        Initialise the cache.

        Args:
            max_size: Maximum number of entries before LRU eviction kicks in.
            ttl_seconds: Seconds after which a cache entry is considered stale.
        """
        self._max_size = max_size
        self._ttl = ttl_seconds
        # OrderedDict gives O(1) LRU move-to-end and FIFO eviction
        self._store: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve a cached result.

        Returns a deep copy so that callers can freely mutate the returned
        dict (e.g. add ``processing_time_ms``) without affecting the stored
        entry.

        Args:
            key: Cache key produced by :func:`compute_cache_key`.

        Returns:
            A deep copy of the cached result dict, or ``None`` when not found /
            expired.
        """
        with self._lock:
            if key not in self._store:
                return None
            timestamp, result = self._store[key]
            if time.monotonic() - timestamp > self._ttl:
                # Expired – remove and report miss
                del self._store[key]
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return copy.deepcopy(result)

    def set(self, key: str, result: dict[str, Any]) -> None:
        """
        Store a result in the cache.

        A deep copy of ``result`` is stored so that subsequent mutations by
        the caller do not corrupt the cached value.

        Note: if the key already exists, its TTL is reset to the current
        time.  This is intentional – analysis results are deterministic, so
        re-caching the same key is essentially a no-op that refreshes the
        expiry.

        Args:
            key: Cache key produced by :func:`compute_cache_key`.
            result: Analysis result dict (only aggregate metrics, no image data).
        """
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (time.monotonic(), copy.deepcopy(result))
            # Evict oldest entry when over capacity
            if len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        """Current number of entries in the cache."""
        with self._lock:
            return len(self._store)
