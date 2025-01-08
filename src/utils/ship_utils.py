import re

import discord

from src.config.ships import SHIPS
from src.data.structs import Ship


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

SHIP_NAME_PATTERN = r"\b(USS[\s][^\s,\.]+)\b"
FIND_WITHIN = 25

def get_main_ship_from_content(content: str, ships: [Ship] = SHIPS) -> str or None:
    """
    Get the main ship name from the content.
    1. If sailing on an auxiliary ship, the main ship name is the second ship name found.
    2. If sailing on the main ship, the main ship name is the first ship name found.
    3. The main ship name must match one of the ship roles.

    Returns:
        str: The main ship name if found, None otherwise.
    """
    first_25_words = " ".join(content.split()[:FIND_WITHIN]).replace("*", "").replace("_", "")
    matches = re.findall(SHIP_NAME_PATTERN, first_25_words)
    main_ship = None

    # If only one ship name is found, assume it is the main ship
    if len(matches) == 1:
        main_ship = matches[0]
    # If two ship names are found, assume the first one is the auxiliary ship
    # And thus the second one is the main ship
    elif len(matches) >= 2:
        main_ship = matches[1]

    if not main_ship:
        return None

    # Check if the main ship name matches one of the ship roles
    for ship in ships:
        if main_ship.upper() == ship.name.upper():
            return ship.name

    return None

def get_auxiliary_ship_from_content(content: str) -> str or None:
    """
    Get the auxiliary ship name from the content.
    1. If sailing on an auxiliary ship, the auxiliary ship name is the first ship name found.
    2. There must be at least two ship names found in the content. The second one being a main ship.

    Returns:
        str: The auxiliary ship name if found, None otherwise.
    """
    first_25_words = " ".join(content.split()[:FIND_WITHIN]).replace("*", "").replace("_", "")
    matches = re.findall(SHIP_NAME_PATTERN, first_25_words)
    auxiliary_ship = None

    # If two ship names are found, assume the first one is the auxiliary ship
    if len(matches) >= 2:
        auxiliary_ship = matches[0]

    return auxiliary_ship


def get_count_from_content(content: str) -> int:
    """
    Returns:
        int: The count if found, -1 otherwise.
    """
    first_25_words = " ".join(content.split()[:FIND_WITHIN])
    count_pattern = r"\b(\d+)(st|nd|rd|th|\s)\b"
    matches = re.findall(count_pattern, first_25_words)
    if not matches:
        return -1

    return int(matches[0][0])

def convert_to_ordinal(count: int) -> str:
    if 10 <= count % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(count % 10, "th")
    return f"{count}{suffix}"
