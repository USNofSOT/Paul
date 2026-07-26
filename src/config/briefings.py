from datetime import UTC, time
from typing import Final

from src.config.main_server import BOT_TEST_COMMAND
from src.config.ranks_roles import NCO_AND_UP_PURE, VOYAGE_PERMISSIONS
from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)

DAILY_BRIEFING_ENABLED: Final[bool] = True
DAILY_BRIEFING_TIME: Final[time] = time(hour=15, minute=0, tzinfo=UTC)
DAILY_VOYAGE_DUE_SOON_DAYS: Final[int] = 7
DAILY_HOSTING_DUE_SOON_DAYS: Final[int] = 3
DAILY_AVATAR_SIZE: Final[int] = 64
DAILY_AVATAR_FETCH_TIMEOUT_SECONDS: Final[float] = 3.0
DAILY_BRIEFING_CONCERNS: Final[dict[str, bool]] = {
    "requirements": True,
    "awards": True,
}

WEEKLY_BRIEFING_ENABLED: Final[bool] = True
WEEKLY_BRIEFING_TIME: Final[time] = time(hour=9, minute=0, tzinfo=UTC)
WEEKLY_BRIEFING_WEEKDAY: Final[int] = 4  # Friday
WEEKLY_BRIEFING_POINT_COUNT: Final[int] = 4
WEEKLY_BRIEFING_BUCKET_DAYS: Final[int] = 7
WEEKLY_BRIEFING_CONCERNS: Final[dict[str, bool]] = {
    "activity": True,
    "crew": True,
}

BRIEFING_VOYAGE_REQUIREMENT_DAYS: Final[int] = VOYAGING_REQUIREMENT_IN_DAYS
BRIEFING_HOSTING_REQUIREMENT_DAYS: Final[int] = HOSTING_REQUIREMENT_IN_DAYS
BRIEFING_PREVIEW_CHANNEL_ID: Final[int] = BOT_TEST_COMMAND
HOST_CAPABLE_ROLE_IDS: Final[frozenset[int]] = frozenset(
    (*NCO_AND_UP_PURE, VOYAGE_PERMISSIONS)
)
