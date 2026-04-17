import logging
import time
from typing import Set, Dict, Tuple

import discord

from .hierarchy import ROLE_HIERARCHY
from .repository import UserRoleRepository
from .roles import DISCORD_ROLE_MAP

log = logging.getLogger(__name__)

# Cache stores {user_id: (roles, expiry_timestamp)}
_role_cache: Dict[int, Tuple[Set[str], float]] = {}
CACHE_TTL = 300  # 5 minutes


def resolve_effective_roles(member: discord.Member) -> Set[str]:
    """
    Resolves the effective roles for a member, combining Discord roles, 
    database-assigned roles, and their hierarchical expansions.
    
    Args:
        member (discord.Member): The Discord member to evaluate.
        
    Returns:
        Set[str]: A set of role names representing the member's effective permissions.
    """
    now = time.time()

    # 1. Check TTL Cache
    if member.id in _role_cache:
        roles, expiry = _role_cache[member.id]
        if now < expiry:
            return roles

    effective_roles: Set[str] = set()

    # 2. Resolve Discord Roles
    for role in member.roles:
        if role.id in DISCORD_ROLE_MAP:
            effective_roles.add(DISCORD_ROLE_MAP[role.id])

    # 3. Resolve Database Roles (Fail-to-Safety)
    try:
        with UserRoleRepository() as repo:
            db_roles = repo.get_user_roles(member.id)
            effective_roles.update(db_roles)
    except Exception as e:
        # If the DB is unreachable, we log a critical error but continue 
        # with the roles already resolved from Discord to ensure the bot 
        # stays functional.
        log.critical(
            "Security DB unreachable! Falling back to Discord roles for %s: %s",
            member.id,
            e
        )

    # 4. Expand Roles via Hierarchy
    # We iterate over a copy of the current effective roles to avoid 
    # modification issues, though we're building a new set anyway.
    expanded_roles = set(effective_roles)
    for role in effective_roles:
        if role in ROLE_HIERARCHY:
            expanded_roles.update(ROLE_HIERARCHY[role])

    # 5. Update Cache and Return
    _role_cache[member.id] = (expanded_roles, now + CACHE_TTL)
    return expanded_roles


def clear_role_cache(user_id: int = None):
    """
    Clears the role cache for a specific user or the entire cache.
    
    Args:
        user_id (int, optional): The Discord ID of the user to clear from cache. 
                                If None, the entire cache is cleared.
    """
    global _role_cache
    if user_id:
        _role_cache.pop(user_id, None)
    else:
        _role_cache = {}
