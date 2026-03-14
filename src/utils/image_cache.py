from __future__ import annotations

import hashlib
import inspect
import io
import json
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from logging import getLogger
from pathlib import Path
from typing import Any

import discord
from matplotlib import pyplot as plt

from src.config.cache import ImageCacheConfig

log = getLogger(__name__)


@dataclass(frozen=True)
class CacheCleanupResult:
    cache_name: str
    removed_expired: int
    removed_overflow: int
    remaining_items: int


@dataclass(frozen=True)
class CacheStatsSnapshot:
    cache_name: str
    request_count: int
    cache_hit_count: int
    cache_miss_count: int
    cached_percent: float


class CacheStatsRecorder:
    def record_request(
            self,
            cache_name: str,
            was_hit: bool,
    ) -> CacheStatsSnapshot | None:
        repository = None
        try:
            from src.data.repository.cache_stats_repository import CacheStatsRepository

            repository = CacheStatsRepository()
        except Exception as e:
            log.warning("Unable to record cache stats for %s: %s", cache_name, e)
            return None

        try:
            cache_stat = repository.record_request(cache_name, was_hit)
            snapshot = CacheStatsSnapshot(
                cache_name=cache_stat.cache_name,
                request_count=cache_stat.request_count,
                cache_hit_count=cache_stat.cache_hit_count,
                cache_miss_count=cache_stat.cache_miss_count,
                cached_percent=cache_stat.cached_percent,
            )
            return snapshot
        except Exception as e:
            log.warning("Unable to record cache stats for %s: %s", cache_name, e)
            return None
        finally:
            if repository is not None:
                repository.close_session()


DEFAULT_CACHE_STATS_RECORDER = CacheStatsRecorder()


def _normalize_cache_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, bytes):
        return hashlib.sha256(value).hexdigest()
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_cache_value(nested_value)
            for key, nested_value in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }
    if isinstance(value, set):
        normalized_items = [_normalize_cache_value(item) for item in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(item, sort_keys=True),
        )
    if isinstance(value, list | tuple):
        return [_normalize_cache_value(item) for item in value]
    if hasattr(value, "__dict__"):
        return _normalize_cache_value(vars(value))
    return str(value)


def build_cache_key(payload: Any, *, version: int = 1) -> str:
    normalized_payload = {
        "payload": _normalize_cache_value(payload),
        "version": version,
    }
    raw_key = json.dumps(
        normalized_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class BinaryImageCache:
    def __init__(
            self,
            config: ImageCacheConfig,
            *,
            stats_recorder: CacheStatsRecorder | None = None,
    ):
        self.config = config
        self.directory = Path(config.directory)
        self.stats_recorder = stats_recorder or DEFAULT_CACHE_STATS_RECORDER

    def key_for(self, payload: Any) -> str:
        return build_cache_key(payload, version=self.config.version)

    def path_for(self, payload: Any) -> Path:
        return self.path_for_key(self.key_for(payload))

    def path_for_key(self, key: str) -> Path:
        return self.directory / f"{key}{self.config.extension}"

    def load_bytes(self, payload: Any) -> bytes | None:
        path = self.path_for(payload)
        return self._load_bytes_from_path(path)

    def _load_bytes_from_path(self, path: Path) -> bytes | None:
        if not path.exists():
            return None
        data = path.read_bytes()
        path.touch()
        return data

    def save_bytes(self, payload: Any, data: bytes) -> bytes:
        path = self.path_for(payload)
        return self._save_bytes_to_path(path, data)

    def _save_bytes_to_path(self, path: Path, data: bytes) -> bytes:
        self.directory.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data

    def get_or_create_bytes(
            self,
            payload: Any,
            producer: Callable[[], bytes | None],
    ) -> bytes | None:
        key = self.key_for(payload)
        path = self.path_for_key(key)
        cached = self._load_bytes_from_path(path)
        if cached is not None:
            self._log_cache_usage(key=key, path=path, was_hit=True, data=cached)
            return cached

        data = producer()
        if data is None:
            stats = self._record_request(was_hit=False)
            self._log_cache_miss(key=key, path=path, data_size=0, stats=stats)
            return None

        self._save_bytes_to_path(path, data)
        stats = self._record_request(was_hit=False)
        self._log_cache_miss(
            key=key,
            path=path,
            data_size=len(data),
            stats=stats,
        )
        log.info(
            "Cache saved [%s] key=%s path=%s size_bytes=%s",
            self.config.name,
            key,
            path,
            len(data),
        )
        return data

    async def get_or_create_bytes_async(
            self,
            payload: Any,
            producer: Callable[[], bytes | None | Awaitable[bytes | None]],
    ) -> bytes | None:
        key = self.key_for(payload)
        path = self.path_for_key(key)
        cached = self._load_bytes_from_path(path)
        if cached is not None:
            self._log_cache_usage(key=key, path=path, was_hit=True, data=cached)
            return cached

        data = producer()
        if inspect.isawaitable(data):
            data = await data
        if data is None:
            stats = self._record_request(was_hit=False)
            self._log_cache_miss(key=key, path=path, data_size=0, stats=stats)
            return None

        self._save_bytes_to_path(path, data)
        stats = self._record_request(was_hit=False)
        self._log_cache_miss(
            key=key,
            path=path,
            data_size=len(data),
            stats=stats,
        )
        log.info(
            "Cache saved [%s] key=%s path=%s size_bytes=%s",
            self.config.name,
            key,
            path,
            len(data),
        )
        return data

    def to_discord_file(
            self,
            data: bytes,
            *,
            filename: str | None = None,
    ) -> discord.File:
        buffer = io.BytesIO(data)
        buffer.seek(0)
        return discord.File(buffer, filename=filename or self.config.default_filename)

    def _record_request(self, *, was_hit: bool) -> CacheStatsSnapshot | None:
        return self.stats_recorder.record_request(self.config.name, was_hit)

    def _log_cache_miss(
            self,
            *,
            key: str,
            path: Path,
            data_size: int,
            stats: CacheStatsSnapshot | None,
    ) -> None:
        if stats is None:
            log.info(
                "Cache miss [%s] key=%s path=%s size_bytes=%s",
                self.config.name,
                key,
                path,
                data_size,
            )
            return

        log.info(
            "Cache miss [%s] key=%s path=%s size_bytes=%s requests=%s hits=%s misses=%s cached_percent=%s",
            self.config.name,
            key,
            path,
            data_size,
            stats.request_count,
            stats.cache_hit_count,
            stats.cache_miss_count,
            stats.cached_percent,
        )

    def _log_cache_usage(
            self,
            *,
            key: str,
            path: Path,
            was_hit: bool,
            data: bytes,
    ) -> None:
        stats = self._record_request(was_hit=was_hit)
        if stats is None:
            log.info(
                "Cache %s [%s] key=%s path=%s size_bytes=%s",
                "hit" if was_hit else "miss",
                self.config.name,
                key,
                path,
                len(data),
            )
            return

        log.info(
            "Cache %s [%s] key=%s path=%s size_bytes=%s requests=%s hits=%s misses=%s cached_percent=%s",
            "hit" if was_hit else "miss",
            self.config.name,
            key,
            path,
            len(data),
            stats.request_count,
            stats.cache_hit_count,
            stats.cache_miss_count,
            stats.cached_percent,
        )


def render_matplotlib_plot_to_png(plotter: Callable[[], None]) -> bytes:
    buffer = io.BytesIO()
    try:
        plotter()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        return buffer.getvalue()
    finally:
        plt.close()


def get_cached_item_count(config: ImageCacheConfig) -> int:
    directory = Path(config.directory)
    if not directory.exists():
        return 0
    return len(
        [
            path for path in directory.glob(f"*{config.extension}")
            if path.is_file()
        ]
    )


def clear_cached_items(config: ImageCacheConfig) -> int:
    directory = Path(config.directory)
    if not directory.exists():
        return 0

    removed_items = 0
    for cache_file in directory.glob(f"*{config.extension}"):
        if cache_file.is_file():
            cache_file.unlink(missing_ok=True)
            removed_items += 1
    log.info("Cleared cache items [%s] removed=%s", config.name, removed_items)
    return removed_items


def cleanup_cache(
        config: ImageCacheConfig,
        *,
        now: float | None = None,
) -> CacheCleanupResult:
    directory = Path(config.directory)
    if not directory.exists():
        return CacheCleanupResult(
            cache_name=config.name,
            removed_expired=0,
            removed_overflow=0,
            remaining_items=0,
        )

    now = time.time() if now is None else now
    cache_files = [
        path for path in directory.glob(f"*{config.extension}") if path.is_file()
    ]

    removed_expired = 0
    for cache_file in list(cache_files):
        age_seconds = now - cache_file.stat().st_mtime
        if config.ttl_seconds is not None and age_seconds > config.ttl_seconds:
            cache_file.unlink(missing_ok=True)
            cache_files.remove(cache_file)
            removed_expired += 1

    removed_overflow = 0
    if config.max_items is not None and len(cache_files) > config.max_items:
        cache_files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        for cache_file in cache_files[config.max_items:]:
            cache_file.unlink(missing_ok=True)
            removed_overflow += 1
        cache_files = cache_files[: config.max_items]

    result = CacheCleanupResult(
        cache_name=config.name,
        removed_expired=removed_expired,
        removed_overflow=removed_overflow,
        remaining_items=len(cache_files),
    )
    log.info(
        "Cache cleanup [%s] expired=%s overflow=%s remaining=%s",
        result.cache_name,
        result.removed_expired,
        result.removed_overflow,
        result.remaining_items,
    )
    return result
