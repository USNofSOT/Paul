from __future__ import annotations

from datetime import UTC, time
from typing import Final

# Daily tasks are intentionally staggered to reduce burst load on the guild and DB.
TRACK_SHIP_SIZE_TASK_TIME: Final[time] = time(hour=0, minute=3, tzinfo=UTC)
COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS: Final[int] = 24
COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS: Final[int] = 26
CHECK_AWARDS_TASK_TIME: Final[time] = time(hour=15, minute=5, tzinfo=UTC)
CHECK_TRAINING_AWARDS_TASK_TIME: Final[time] = time(hour=15, minute=12, tzinfo=UTC)

IMAGE_CACHE_JANITOR_TASK_INTERVAL_HOURS: Final[int] = 6
COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS: Final[int] = 300  # 5 minutes
