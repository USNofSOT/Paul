from __future__ import annotations

from datetime import UTC, time
from typing import Final

# Daily tasks are intentionally staggered to reduce burst load on the guild and DB.
TRACK_ROLE_SIZE_TASK_TIME: Final[time] = time(hour=0, minute=1, tzinfo=UTC)
CHECK_BOA_AWARDS_TASK_TIME: Final[time] = time(hour=15, minute=5, tzinfo=UTC)
CHECK_TRAINING_AWARDS_TASK_TIME: Final[time] = time(hour=15, minute=12, tzinfo=UTC)
CHECK_REPRESENTATION_AWARDS_TASK_TIME: Final[time] = time(
    hour=15, minute=18, tzinfo=UTC
)

IMAGE_CACHE_JANITOR_TASK_INTERVAL_HOURS: Final[int] = 6
HEALTH_SNAPSHOT_INTERVAL_MINUTES: Final[int] = 5
DISCORD_MEMBER_SYNC_TASK_INTERVAL_HOURS: Final[int] = 24
