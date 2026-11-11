"""
Asynchronous Task Queue configuration using Huey.
Defaults to SqliteHuey for zero-daemon local execution, with seamless one-line upgrade to RedisHuey.
Falls back to synchronous execution if huey is not installed.
"""
from pathlib import Path
from typing import Optional, Callable, Any
import logging

from opengen.config import settings

logger = logging.getLogger(__name__)

try:
    from huey import SqliteHuey, RedisHuey
    _HAS_HUEY = True
except ImportError:
    _HAS_HUEY = False


class _FallbackQueue:
    """Synchronous fallback queue when huey is not installed."""
    def task(self, *args, **kwargs):
        def decorator(fn: Callable) -> Callable:
            fn.schedule = fn
            return fn
        return decorator


def init_queue(queue_db_path: Optional[Path] = None):
    """Initializes Huey queue instance based on configuration."""
    if not _HAS_HUEY:
        logger.info("Huey not installed; using synchronous in-process task execution")
        return _FallbackQueue()

    if settings.QUEUE_BACKEND == "redis":
        return RedisHuey("opengen_tasks", url=settings.REDIS_URL)
    else:
        db_file = queue_db_path or (settings.CACHE_DIR / "queue.db")
        db_file.parent.mkdir(parents=True, exist_ok=True)
        return SqliteHuey("opengen_tasks", filename=str(db_file))


huey = init_queue()
