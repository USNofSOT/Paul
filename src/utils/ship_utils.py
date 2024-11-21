import discord

from src.config.ships import SHIPS


def get_ship_role_id_by_member(member: discord.Member) -> int:
    """
    Get the first ship role ID that the member has.

    Args:
        member (discord.Member): The member to check for roles.
    Returns:
        int: The role ID of the ship, or -1 if the member has no ship roles. -2 if member is None.
    """
    if not member:
        return -2
    for ship in SHIPS:
        if ship.role_id in [role.id for role in member.roles]:
            return ship.role_id
    return -1

def get_ship_by_role_id(role_id: int) -> dict or None:
    """
    Get the ship object by role ID.
    """
    for ship in SHIPS:
        if ship.role_id == role_id:
            return ship
    return None