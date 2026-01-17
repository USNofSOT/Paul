from datetime import datetime
from logging import getLogger

import discord
from discord.ext import commands

from src.config import GUILD_ID, ENGINEERS
from src.utils.embeds import error_embed

log= getLogger(__name__)

async def alert_engineers(bot: commands.Bot, message: str, exception: Exception = None):
    guild = bot.get_guild(GUILD_ID)
    engineers = ENGINEERS

    embed = error_embed(
        title="Unexpected Error Occurred",
        description=f"{message}",
        exception=exception
    )
    embed.timestamp = datetime.now()

    # DM all engineers
    for engineer_id in engineers:
        engineer = guild.get_member(engineer_id)
        if engineer:
            try:
                await engineer.send(embed=embed)
            except discord.HTTPException:
                log.error(f"Error sending alert to engineer {engineer_id}")

    # Message in bot-test-command

    test_channel = guild.get_channel(1291589569602650154)
    if test_channel:
        try:
            await test_channel.send(embed=embed)
        except discord.HTTPException:
            log.error("Error sending alert to bot-test-command channel")



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