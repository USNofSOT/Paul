import logging
from typing import Optional

from src.data import CacheStat
from src.data.repository.common.base_repository import BaseRepository, Session
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class CacheStatsRepository(BaseRepository[CacheStat]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(CacheStat, session)

    def _get_or_create_cache_stat(self, cache_name: str) -> CacheStat:
        cache_stat = (
            self.session.query(CacheStat)
            .filter(CacheStat.cache_name == cache_name)
            .first()
        )
        if cache_stat is None:
            cache_stat = CacheStat(
                cache_name=cache_name,
                request_count=0,
                cache_hit_count=0,
                cache_miss_count=0,
                cached_percent=0,
                janitor_run_count=0,
                janitor_removed_expired_count=0,
                janitor_removed_overflow_count=0,
                janitor_last_removed_expired=0,
                janitor_last_removed_overflow=0,
                janitor_last_remaining_items=0,
            )
        return cache_stat

    def record_request(self, cache_name: str, was_hit: bool) -> CacheStat:
        try:
            cache_stat = self._get_or_create_cache_stat(cache_name)
            now = utc_time_now()

            cache_stat.request_count += 1
            cache_stat.last_requested_at = now

            if was_hit:
                cache_stat.cache_hit_count += 1
                cache_stat.last_cache_hit_at = now
            else:
                cache_stat.cache_miss_count += 1
                cache_stat.last_cache_miss_at = now

            cache_stat.cached_percent = round(
                (cache_stat.cache_hit_count / cache_stat.request_count) * 100,
                2,
            )

            self.session.add(cache_stat)
            self.session.commit()
            return cache_stat
        except Exception as e:
            self.session.rollback()
            log.error("Error recording cache stats for %s: %s", cache_name, e)
            raise e

    def record_janitor_run(
            self,
            cache_name: str,
            *,
            removed_expired: int,
            removed_overflow: int,
            remaining_items: int,
    ) -> CacheStat:
        try:
            cache_stat = self._get_or_create_cache_stat(cache_name)
            cache_stat.janitor_run_count += 1
            cache_stat.janitor_removed_expired_count += removed_expired
            cache_stat.janitor_removed_overflow_count += removed_overflow
            cache_stat.janitor_last_removed_expired = removed_expired
            cache_stat.janitor_last_removed_overflow = removed_overflow
            cache_stat.janitor_last_remaining_items = remaining_items
            cache_stat.janitor_last_run_at = utc_time_now()

            self.session.add(cache_stat)
            self.session.commit()
            return cache_stat
        except Exception as e:
            self.session.rollback()
            log.error("Error recording janitor stats for %s: %s", cache_name, e)
            raise e

    def get_cache_stat(self, cache_name: str) -> CacheStat | None:
        try:
            return (
                self.session.query(CacheStat)
                .filter(CacheStat.cache_name == cache_name)
                .first()
            )
        except Exception as e:
            self.session.rollback()
            log.error("Error getting cache stats for %s: %s", cache_name, e)
            raise e

    def clear_all_cache_stats(self) -> int:
        try:
            deleted_rows = self.session.query(CacheStat).delete()
            self.session.commit()
            return deleted_rows
        except Exception as e:
            self.session.rollback()
            log.error("Error clearing cache stats: %s", e)
            raise e
