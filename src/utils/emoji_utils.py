from __future__ import annotations

from src.config.emojis import USNSOT_EMOJI
from src.data.structs import Ship
from src.utils.ship_utils import get_ship_by_role_id


def resolve_ship_emoji(
        *,
        ship_role_id: int | None = None,
        ship: Ship | None = None,
        fallback: str = USNSOT_EMOJI,
) -> str:
    resolved_ship = ship or (
        get_ship_by_role_id(ship_role_id) if ship_role_id is not None else None
    )
    if resolved_ship and resolved_ship.emoji:
        return resolved_ship.emoji
    return fallback


def render_ship_label(
        *,
        ship_role_id: int | None = None,
        ship: Ship | None = None,
        fallback_name: str = "Unknown ship",
) -> str:
    resolved_ship = ship or (
        get_ship_by_role_id(ship_role_id) if ship_role_id is not None else None
    )
    emoji = resolve_ship_emoji(ship_role_id=ship_role_id, ship=resolved_ship)
    ship_name = resolved_ship.name if resolved_ship and resolved_ship.name else fallback_name
    return f"{emoji} {ship_name}"
