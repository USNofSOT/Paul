"""
Generic embeds for the bot.
"""
import discord

from discord.ext import commands
from discord.ext.commands.parameters import empty


def default_embed(title: str = None, description: str = None):
    """
    Create a default embed.

    Args:
        title (str): The title of the embed.
        description (str): The description of the embed.
    Returns:
        discord.Embed: The default embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue(),
    )
    embed.set_author(
        name="The United States Navy SoT"
    )
    return embed

def error_embed(description: str, exception: Exception = None):
    """
    Create a generic error embed.

    Args:
        description (str): The description of the error.
        exception (Exception): The error identifier. Commonly a python exception.
    Returns:
        discord.Embed: The error embed
    """
    embed = discord.Embed(
        title="Error occurred",
        description=description,
        color=discord.Color.red(),
    )
    embed.set_footer(text="If this issue persists, please contact the NCS Department.")

    if exception:
        embed.add_field(name="Error Type", value=exception.__class__.__name__)
        embed.add_field(name="Error Message", value=str(exception))

    return embed
