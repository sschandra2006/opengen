"""
Persistent L2 disk caching using diskcache.FanoutCache.
Provides fast LRU-evicted caching for template profiles, extractions, and prompt results.
"""
from pathlib import Path
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

try:
    import diskcache
    _HAS_DISKCACHE = True
except ImportError:
    _HAS_DISKCACHE = False


class _InMemoryFallbackCache:
    """Fallback cache when diskcache is not installed."""
    def __init__(self):
        self._store: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def set(self, key: str, value: Any, expire: Optional[int] = None, tag: Optional[str] = None):
        self._store[key] = value

    def delete(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def close(self):
        pass


class DiskCacheManager:
    """Manages disk cache with LRU eviction and graceful in-memory fallback."""

    _instance: Optional["DiskCacheManager"] = None

    def __init__(self, cache_dir: Optional[Path] = None):
        from opengen.config import settings
        self.cache_dir = cache_dir or (settings.CACHE_DIR / "l2_diskcache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if _HAS_DISKCACHE:
            # 5 GB limit with 4 shards for high-concurrency throughput
            self.cache = diskcache.FanoutCache(str(self.cache_dir), shards=4, size_limit=5 * 1024 * 1024 * 1024)
        else:
            self.cache = _InMemoryFallbackCache()

    @classmethod
    def get_instance(cls) -> "DiskCacheManager":
        if cls._instance is None:
            cls._instance = DiskCacheManager()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Used in test fixtures to reset cache directory."""
        if cls._instance:
            try:
                cls._instance.cache.close()
            except Exception:
                pass
        cls._instance = None

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any, expire: Optional[int] = None, tag: Optional[str] = None):
        self.cache.set(key, value, expire=expire, tag=tag)

    def delete(self, key: str):
        self.cache.delete(key)

    def clear(self):
        self.cache.clear()

    # Domain-specific helpers
    def get_template_profile(self, file_hash: str) -> Optional[Dict[str, Any]]:
        return self.get(f"template:profile:{file_hash}")

    def set_template_profile(self, file_hash: str, profile_dict: Dict[str, Any]):
        self.set(f"template:profile:{file_hash}", profile_dict, tag="template")

    def get_reference_extraction(self, file_hash: str) -> Optional[Dict[str, Any]]:
        return self.get(f"reference:extract:{file_hash}")

    def set_reference_extraction(self, file_hash: str, extract_dict: Dict[str, Any]):
        self.set(f"reference:extract:{file_hash}", extract_dict, tag="reference")

    def get_image_cache(self, prompt_hash: str) -> Optional[str]:
        return self.get(f"image:hash:{prompt_hash}")

    def set_image_cache(self, prompt_hash: str, file_path: str):
        self.set(f"image:hash:{prompt_hash}", file_path, tag="image")


class _CacheManagerProxy:
    """Lazy proxy delegating to the active DiskCacheManager instance (supports clean test resets)."""

    def __getattr__(self, item: str) -> Any:
        return getattr(DiskCacheManager.get_instance(), item)


cache_manager: DiskCacheManager = _CacheManagerProxy()  # type: ignore
