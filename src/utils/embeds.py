"""
Generic embeds for the bot.
"""

from enum import StrEnum

import discord


def marine_embed() -> discord.Embed:
    embed = discord.Embed(
        title="United States Marine Corps (USMC)",
        color=discord.Color.from_rgb(192, 3, 44),
    )
    embed.set_author(
        name="Office of the Marine Commandant",
        icon_url="https://cdn.discordapp.com/emojis/1083000667527970867.png",
    )

    return embed


def member_embed(member: discord.Member) -> discord.Embed:
    embed = default_embed(
        title=f"{member.display_name or member.name}",
        description=f"{member.mention}",
        author=False,
    )

    try:
        avatar_url = (
            member.guild_avatar.url if member.guild_avatar else member.avatar.url
        )
        embed.set_thumbnail(url=avatar_url)
    except AttributeError:
        pass

    return embed


def default_embed(
    title: str = None, description: str = None, author: bool = True
) -> discord.Embed:
    """
    Create a default embed.

    Args:
        title (str): The title of the embed.
        description (str): The description of the embed.
        author (bool): Whether to include the author message.
    Returns:
        discord.Embed: The default embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue(),
    )
    if author:
        embed.set_author(name="The United States Navy SoT")
    return embed


def error_embed(
    title: str = "Error occurred",
    description: str = "Something went wrong...",
    exception: Exception = None,
    footer: bool = True,
):
    """
    Create a generic error embed.

    Args:
        title (str): The title of the error.
        description (str): The description of the error.
        exception (Exception): The error identifier. Commonly a python exception.
        footer (bool): Whether to include the footer message.
    Returns:
        discord.Embed: The error embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red(),
    )

    if footer:
        embed.set_footer(
            text="If this issue persists, please contact the NSC Department."
        )

    if exception:
        embed.add_field(name="Error Type", value=exception.__class__.__name__)
        embed.add_field(name="Error Message", value=str(exception))

    return embed


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def engineer_alert_embed(
        *,
        severity: AlertSeverity,
        title: str,
        description: str,
        exception: Exception = None,
        fields: tuple[tuple[str, str], ...] = (),
        footer: bool = True,
) -> discord.Embed:
    color_map = {
        AlertSeverity.INFO: discord.Color.blue(),
        AlertSeverity.WARNING: discord.Color.orange(),
        AlertSeverity.ERROR: discord.Color.red(),
        AlertSeverity.CRITICAL: discord.Color.dark_red(),
    }
    embed = discord.Embed(
        title=f"[{severity.value}] {title}",
        description=description,
        color=color_map[severity],
    )
    embed.set_author(name="Paul Engineer Alerts")

    for field_name, field_value in fields:
        embed.add_field(name=field_name, value=field_value, inline=False)

    if exception:
        embed.add_field(name="Error Type", value=exception.__class__.__name__)
        embed.add_field(name="Error Message", value=str(exception), inline=False)

    if footer:
        embed.set_footer(text="Engineer alert stream")

    return embed
