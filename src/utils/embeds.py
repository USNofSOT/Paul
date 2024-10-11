"""
Generic embeds for the bot.
"""
import discord

from discord.ext import commands


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
