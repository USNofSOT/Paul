"""
Generic embeds for the bot.
"""
import discord

def member_embed(member: discord.Member) -> discord.Embed:
    embed = default_embed(
        title=f"{member.display_name or member.name}",
        description=f"{member.mention}",
        author=False
    )

    try:
        avatar_url = member.guild_avatar.url if member.guild_avatar else member.avatar.url
        embed.set_thumbnail(url=avatar_url)
    except AttributeError:
        pass

    return embed

def default_embed(title: str = None, description: str = None, author: bool  = True) -> discord.Embed:
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
        embed.set_author(
            name="The United States Navy SoT"
        )
    return embed

def error_embed(title: str = "Error occurred", description: str = "Something went wrong...", exception: Exception = None, footer: bool = True):
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
        embed.set_footer(text="If this issue persists, please contact the NSC Department.")

    if exception:
        embed.add_field(name="Error Type", value=exception.__class__.__name__)
        embed.add_field(name="Error Message", value=str(exception))

    return embed
