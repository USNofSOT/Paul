from logging import getLogger

import discord
from discord.ext import commands

from src.config import GUILD_ID

log= getLogger(__name__)

def get_best_display_name(bot: commands.Bot, discord_id: int):
    """
    Get the best display name for a user

    The priority is as follows:
    1. Guild display name
    2. Gamer tag outside of guild
    3. Unknown with Discord ID (if all else fails)

    Args:
        bot (commands.Bot): The bot instance.
        discord_id (int): The Discord ID of the user.
    Returns:
        str: The best display name for the user.
    """

    try:
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(discord_id)

        # 1. Attempt to get the guild display name
        if member:
            return member.nick or member.name

        # 2. Attempt to get the user's gamertag
        user = bot.get_user(discord_id)
        if user:
            return user.name + " (User not in guild)"

        # 3. Fallback to unknown
        return f"Unknown ({discord_id})"

    except discord.HTTPException:
        # Handle potential errors (missing intents or API errors)
        log.error("Error retrieving member information. Please ensure necessary intents are enabled.")
        return "Unknown (Error)"