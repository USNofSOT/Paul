from __future__ import annotations

from src.config.notifications import NotificationRolloutMap
from src.notifications.types import NotificationType, ResolvedMemberContext


def is_notification_enabled_for_member(
        rollout_map: NotificationRolloutMap,
        notification_type: NotificationType,
        member_context: ResolvedMemberContext,
) -> bool:
    if member_context.ship_role_id is None:
        return False

    scoped_ships = rollout_map.get(notification_type, {})
    if member_context.ship_role_id not in scoped_ships:
        return False

    enabled_squads = scoped_ships[member_context.ship_role_id]
    if not enabled_squads:
        return True

    return member_context.squad_role_id in enabled_squads
