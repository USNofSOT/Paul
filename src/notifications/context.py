from __future__ import annotations

import discord

from src.config.ranks_roles import SHIP_SL_ROLE
from src.notifications.types import ResolvedMemberContext
from src.utils.ship_utils import get_ship_by_role_id, get_ship_role_id_by_member


def get_squad_role(member: discord.Member) -> discord.Role | None:
    for role in member.roles:
        if "Squad" in role.name and role.id != SHIP_SL_ROLE:
            return role
    return None


def build_member_context(member: discord.Member) -> ResolvedMemberContext:
    ship_role_id = get_ship_role_id_by_member(member)
    ship = get_ship_by_role_id(ship_role_id) if ship_role_id and ship_role_id > 0 else None
    squad_role = get_squad_role(member)
    return ResolvedMemberContext(
        sailor_id=member.id,
        display_name=member.display_name or member.name,
        ship_role_id=ship_role_id if ship_role_id and ship_role_id > 0 else None,
        ship_name=ship.name if ship else None,
        squad_role_id=squad_role.id if squad_role else None,
        squad_name=squad_role.name if squad_role else None,
        avatar_url=member.display_avatar.url if member.display_avatar else None,
    )
