from __future__ import annotations

from discord import Guild

from src.config.notifications import NOTIFICATION_CHANNEL_OVERRIDES
from src.notifications.types import (
    NotificationDefinition,
    ResolvedMemberContext,
    ResolvedRoute,
)
from src.utils.ship_utils import get_ship_by_role_id


class ShipCommandRouteResolver:
    def resolve(
            self,
            definition: NotificationDefinition,
            member_context: ResolvedMemberContext,
            guild: Guild,
    ) -> ResolvedRoute:
        del definition

        if member_context.ship_role_id is None:
            return ResolvedRoute(
                destination_channel_id=None,
                skip_reason="missing_ship_role",
            )

        ship = get_ship_by_role_id(member_context.ship_role_id)
        destination_channel_id = NOTIFICATION_CHANNEL_OVERRIDES.get(
            member_context.ship_role_id
        )

        if ship is None and destination_channel_id is None:
            return ResolvedRoute(
                destination_channel_id=None,
                skip_reason="missing_command_channel_config",
            )

        if destination_channel_id is None:
            destination_channel_id = ship.boat_command_channel_id if ship else None

        if destination_channel_id is None:
            return ResolvedRoute(
                destination_channel_id=None,
                skip_reason="missing_command_channel_config",
            )

        if guild.get_channel(destination_channel_id) is None:
            return ResolvedRoute(
                destination_channel_id=None,
                skip_reason="command_channel_not_found",
            )

        return ResolvedRoute(destination_channel_id=destination_channel_id)
