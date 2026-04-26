from __future__ import annotations

import logging
from datetime import UTC, time

import psutil
from discord.ext import commands, tasks

from src.config.task_timing import HEALTH_SNAPSHOT_INTERVAL_MINUTES
from src.data import HealthSnapshot
from src.data.engine import engine
from src.data.repository.health_snapshot_repository import HealthSnapshotRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)

_PROCESS = psutil.Process()

# Generate 5-minute alignment points (00, 05, 10... 55) for every hour.
_SNAPSHOT_TIMES = [
    time(hour=h, minute=m, tzinfo=UTC)
    for h in range(24)
    for m in range(0, 60, HEALTH_SNAPSHOT_INTERVAL_MINUTES)
]


class HealthSnapshotTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snapshot_loop.start()

    def cog_unload(self):
        self.snapshot_loop.cancel()

    @tasks.loop(time=_SNAPSHOT_TIMES)
    async def snapshot_loop(self):
        pool = engine.pool
        repo = HealthSnapshotRepository()
        try:
            # Look back exactly 5 minutes for latency window
            avg_ms, max_ms = repo.get_latency_window(minutes=HEALTH_SNAPSHOT_INTERVAL_MINUTES)

            # Collect additional metrics
            discord_latency = round(self.bot.latency * 1000, 2) if self.bot.latency else None
            bot_cpu = round(_PROCESS.cpu_percent(interval=None), 2)
            sys_cpu = round(psutil.cpu_percent(interval=None), 2)
            sys_mem_mb = round(psutil.virtual_memory().total / (1024 * 1024), 2)
            users = len(self.bot.users)

            snapshot = HealthSnapshot(
                timestamp=utc_time_now(),
                pool_size=pool.size(),
                checked_out=pool.checkedout(),
                overflow=pool.overflow(),
                checked_in=pool.checkedin(),
                avg_cmd_latency=avg_ms,
                max_cmd_latency=max_ms,
                memory_usage_mb=round(_PROCESS.memory_info().rss / (1024 * 1024), 2),
                discord_latency_ms=discord_latency,
                bot_cpu_usage_percent=bot_cpu,
                system_cpu_usage_percent=sys_cpu,
                system_total_memory_mb=sys_mem_mb,
                user_count=users,
            )
            repo.insert_snapshot(snapshot)
        except Exception:
            log.error("Health snapshot failed", exc_info=True)
        finally:
            repo.close_session()

    @snapshot_loop.before_loop
    async def before_snapshot_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(HealthSnapshotTask(bot))
