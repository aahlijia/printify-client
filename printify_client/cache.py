"""Cache manager for Printify API responses."""

import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple


class CacheManager:
    """Thread-safe TTL cache with LRU eviction.

    Provides a simple caching mechanism with time-to-live (TTL) expiration
    and least-recently-used (LRU) eviction when the cache reaches capacity.
    Recency is tracked with an ``OrderedDict`` so both lookups and evictions
    are O(1).

    Args:
        ttl: Time-to-live in seconds for cached items (default: 7200)
        max_size: Maximum number of items to store in cache (default: 128)

    Example:
        >>> cache = CacheManager(ttl=3600, max_size=100)
        >>> cache.set("key1", {"data": "value"})
        >>> result = cache.get("key1")
        >>> cache.clear()
    """

    def __init__(self, ttl: int = 7200, max_size: int = 128):
        """Initialize cache manager with TTL and size limits.

        Args:
            ttl: Time-to-live in seconds for cached items
            max_size: Maximum number of items to store in cache
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: "OrderedDict[str, Tuple[Any, float]]" = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired.

        Checks if the key exists and hasn't expired. If the value is still
        valid, marks it as most recently used and returns the value.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if time.time() > expiry:
                del self._cache[key]
                return None

            # Mark as most recently used
            self._cache.move_to_end(key)

            return value

    def set(self, key: str, value: Any) -> None:
        """Store value with TTL.

        Stores a value in the cache with an expiration time. If the cache
        is at capacity and the key is new, evicts the least recently used
        item before storing the new value.

        Args:
            key: Cache key to store
            value: Value to cache
        """
        with self._lock:
            # If max_size is 0, don't cache anything
            if self.max_size == 0:
                return

            # Evict least recently used item if at capacity
            if key not in self._cache and len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            # Store value and mark as most recently used
            expiry = time.time() + self.ttl
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cached data.

        Removes all items from the cache.
        """
        with self._lock:
            self._cache.clear()
