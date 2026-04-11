from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeAlias

from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.config.ships import ROLE_ID_TITAN, ROLE_ID_VENOM, ROLE_ID_GENESIS
from src.notifications.types import NotificationType, RoutingTargetType, TemplateKey

APPLICATION_TIMEZONE: Final[str] = "UTC"
NOTIFICATION_WORKER_BATCH_SIZE: Final[int] = 25
NOTIFICATION_MAX_DELIVERY_ATTEMPTS: Final[int] = 3
NOTIFICATION_LOOKAHEAD_HOURS: Final[int] = 36
NOTIFICATION_DELIVERY_GRACE_HOURS: Final[int] = 3


@dataclass(frozen=True)
class NotificationDefinitionConfig:
    activity_field: str
    threshold_days: int
    trigger_offsets: tuple[int, ...]
    template_key: TemplateKey
    routing_target: RoutingTargetType


NotificationDefinitionConfigMap: TypeAlias = dict[
    NotificationType, NotificationDefinitionConfig
]
NotificationRolloutMap: TypeAlias = dict[NotificationType, dict[int, tuple[int, ...]]]
NotificationChannelOverrideMap: TypeAlias = dict[int, int]
ShipHealthSummaryRollout: TypeAlias = tuple[int, ...]

NOTIFICATION_DEFINITION_CONFIGS: Final[NotificationDefinitionConfigMap] = {
    NotificationType.NO_VOYAGE_REMINDER: NotificationDefinitionConfig(
        activity_field="last_voyage_at",
        threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
        trigger_offsets=(-7, -3, 0, 7),
        template_key=TemplateKey.NO_VOYAGE_REMINDER,
        routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
    ),
    NotificationType.NO_HOSTING_REMINDER: NotificationDefinitionConfig(
        activity_field="last_hosting_at",
        threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
        trigger_offsets=(-3, 0, 7),
        template_key=TemplateKey.NO_HOSTING_REMINDER,
        routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
    ),
}

# Slow-rollout configuration:
# - ship role absent: disabled
# - ship role present with (): enabled for the whole ship
# - ship role present with squad role IDs: enabled only for those squads on that ship
NOTIFICATION_ROLLOUT: Final[NotificationRolloutMap] = {
    NotificationType.NO_VOYAGE_REMINDER: {
        ROLE_ID_EOS: (),
        ROLE_ID_GLETSJER: (),
        ROLE_ID_NIGHTINGALE: (),
        ROLE_ID_TITAN: (),
        ROLE_ID_VENOM: (),
        ROLE_ID_GENESIS: ()
    },
    NotificationType.NO_HOSTING_REMINDER: {
        ROLE_ID_EOS: (),
        ROLE_ID_GLETSJER: (),
        ROLE_ID_NIGHTINGALE: (),
        ROLE_ID_TITAN: (),
        ROLE_ID_VENOM: (),
        ROLE_ID_GENESIS: ()
    },
}

NOTIFICATION_CHANNEL_OVERRIDES: Final[NotificationChannelOverrideMap] = {}

SHIP_HEALTH_SUMMARY_ENABLED: Final[bool] = True
SHIP_HEALTH_SUMMARY_RECENT_ACTIVITY_DAYS: Final[int] = 7
SHIP_HEALTH_SUMMARY_VOYAGE_DUE_SOON_DAYS: Final[int] = 7
SHIP_HEALTH_SUMMARY_HOSTING_DUE_SOON_DAYS: Final[int] = 3
SHIP_HEALTH_SUMMARY_ROLLOUT: Final[ShipHealthSummaryRollout] = (
    ROLE_ID_TITAN,
    ROLE_ID_VENOM,
    ROLE_ID_GENESIS
)
