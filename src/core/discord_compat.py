from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import discord


def apply_team_member_permissions_compat() -> None:
    original_init = discord.team.TeamMember.__init__
    if getattr(original_init, "__paul_permissions_compat__", False):
        return

    def patched_init(self, team, state, data: Mapping[str, Any]) -> None:
        payload = data
        if "permissions" not in data:
            payload = {**data, "permissions": []}
        original_init(self, team, state, payload)

    patched_init.__paul_permissions_compat__ = True
    discord.team.TeamMember.__init__ = patched_init
