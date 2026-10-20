import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")

log = logging.getLogger(__name__)


def ttl_cache(seconds: int, maxsize: int = 128, cache_name: str | None = None):
    """
    A simple TTL cache decorator that supports memory-based caching with expiration.
    Optionally records stats to the cache repository if cache_name is provided.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: dict[tuple, tuple[float, T]] = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create a cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))

            now = time.time()
            if key in cache:
                expiry, value = cache[key]
                if now < expiry:
                    if cache_name:
                        _record_stats(cache_name, was_hit=True)
                    return value

            # Cache miss or expired
            result = func(*args, **kwargs)
            cache[key] = (now + seconds, result)

            if cache_name:
                _record_stats(cache_name, was_hit=False)

            # Simple overflow protection
            if len(cache) > maxsize:
                # Remove oldest entry
                oldest_key = next(iter(cache))
                del cache[oldest_key]

            return result

        def cache_clear():
            cache.clear()

        wrapper.cache_clear = cache_clear
        return wrapper

    return decorator


def _record_stats(cache_name: str, was_hit: bool) -> None:
    try:
        from src.utils.image_cache import DEFAULT_CACHE_STATS_RECORDER
        DEFAULT_CACHE_STATS_RECORDER.record_request(cache_name, was_hit)
    except Exception as e:
        log.warning("Unable to record memory cache stats for %s: %s", cache_name, e)
