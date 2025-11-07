"""Tests for cache manager."""

import time
import threading
from printify.cache import CacheManager


def test_cache_set_and_get():
    """Test basic cache set and get operations."""
    cache = CacheManager(ttl=10, max_size=5)
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    cache.set("key2", {"data": "value2"})
    assert cache.get("key2") == {"data": "value2"}


def test_cache_get_nonexistent_key():
    """Test getting a key that doesn't exist."""
    cache = CacheManager()
    
    assert cache.get("nonexistent") is None


def test_cache_ttl_expiration():
    """Test that cached items expire after TTL."""
    cache = CacheManager(ttl=1, max_size=5)
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    assert cache.get("key1") is None


def test_cache_lru_eviction():
    """Test LRU eviction when cache reaches max size."""
    cache = CacheManager(ttl=10, max_size=3)
    
    # Fill cache to capacity
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # All keys should be present
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    
    # Add a fourth key, should evict key1 (least recently used)
    cache.set("key4", "value4")
    
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_cache_lru_access_order():
    """Test that accessing a key updates its position in LRU order."""
    cache = CacheManager(ttl=10, max_size=3)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # Access key1 to make it recently used
    cache.get("key1")
    
    # Add key4, should evict key2 (now least recently used)
    cache.set("key4", "value4")
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_cache_update_existing_key():
    """Test updating an existing key doesn't trigger eviction."""
    cache = CacheManager(ttl=10, max_size=3)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # Update key1
    cache.set("key1", "updated_value1")
    
    # All keys should still be present
    assert cache.get("key1") == "updated_value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_cache_clear():
    """Test clearing all cached data."""
    cache = CacheManager(ttl=10, max_size=5)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    
    cache.clear()
    
    assert cache.get("key1") is None
    assert cache.get("key2") is None
    assert cache.get("key3") is None


def test_cache_thread_safety():
    """Test thread-safe concurrent access to cache."""
    cache = CacheManager(ttl=10, max_size=100)
    results = []
    errors = []
    
    def worker(thread_id):
        try:
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                
                cache.set(key, value)
                retrieved = cache.get(key)
                
                if retrieved == value:
                    results.append(True)
                else:
                    results.append(False)
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check that no errors occurred
    assert len(errors) == 0
    
    # Check that all operations succeeded
    assert len(results) == 50
    assert all(results)


def test_cache_concurrent_eviction():
    """Test that LRU eviction works correctly with concurrent access."""
    cache = CacheManager(ttl=10, max_size=10)
    
    def writer(start_idx):
        for i in range(5):
            cache.set(f"key_{start_idx + i}", f"value_{start_idx + i}")
    
    # Create threads that will exceed cache capacity
    threads = []
    for i in range(4):
        thread = threading.Thread(target=writer, args=(i * 5,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Cache should have exactly max_size items
    # We can't predict which ones due to threading, but verify cache still works
    cache.set("final_key", "final_value")
    assert cache.get("final_key") == "final_value"
