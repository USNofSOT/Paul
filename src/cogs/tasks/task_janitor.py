from __future__ import annotations

from logging import getLogger

from discord.ext import commands, tasks

from src.config import IMAGE_CACHES
from src.config.task_timing import IMAGE_CACHE_JANITOR_TASK_INTERVAL_HOURS
from src.data.repository.cache_stats_repository import CacheStatsRepository
from src.utils.image_cache import CacheCleanupResult, cleanup_cache

log = getLogger(__name__)

JANITOR_TARGETS = {
    "ribbon_board": IMAGE_CACHES["ribbon_board"],
    "ribbon_icon": IMAGE_CACHES["ribbon_icon"],
    "crewreport_voyage_chart": IMAGE_CACHES["crewreport_voyage_chart"],
    "crewreport_hosted_chart": IMAGE_CACHES["crewreport_hosted_chart"],
    "netreport_growth_chart": IMAGE_CACHES["netreport_growth_chart"],
    "pocket_watch_activity_chart": IMAGE_CACHES["pocket_watch_activity_chart"],
    "ship_voyages_trend": IMAGE_CACHES["ship_voyages_trend"],
    "ship_hosted_trend": IMAGE_CACHES["ship_hosted_trend"],
    "ship_size_trend": IMAGE_CACHES["ship_size_trend"],
    "health_latency_chart": IMAGE_CACHES["health_latency_chart"],
    "health_connections_chart": IMAGE_CACHES["health_connections_chart"],
    "health_pool_chart": IMAGE_CACHES["health_pool_chart"],
    "health_memory_chart": IMAGE_CACHES["health_memory_chart"],
}


def run_janitor_cleanup(targets=JANITOR_TARGETS) -> dict[str, CacheCleanupResult]:
    return {
        cache_name: cleanup_cache(cache_config)
        for cache_name, cache_config in targets.items()
    }


def persist_janitor_cleanup_results(
        cleanup_results: dict[str, CacheCleanupResult],
) -> None:
    repository = CacheStatsRepository()
    try:
        for cache_name, result in cleanup_results.items():
            repository.record_janitor_run(
                cache_name,
                removed_expired=result.removed_expired,
                removed_overflow=result.removed_overflow,
                remaining_items=result.remaining_items,
            )
    finally:
        repository.close_session()


class Janitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.janitor.start()

    def cog_unload(self):
        self.janitor.cancel()

    @tasks.loop(hours=IMAGE_CACHE_JANITOR_TASK_INTERVAL_HOURS)
    async def janitor(self):
        cleanup_results = run_janitor_cleanup()
        persist_janitor_cleanup_results(cleanup_results)
        for cache_name, result in cleanup_results.items():
            if result.removed_expired or result.removed_overflow:
                log.info(
                    "Janitor cleaned %s: expired=%s overflow=%s remaining=%s",
                    cache_name,
                    result.removed_expired,
                    result.removed_overflow,
                    result.remaining_items,
                )

    @janitor.before_loop
    async def before_janitor(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Janitor(bot))
