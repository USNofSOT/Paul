import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.utils.embeds import error_embed
from .decorators import InsufficientLevelError
from .repository import SecurityInteractionRepository

log = logging.getLogger(__name__)


async def handle_app_command_security_error(interaction: discord.Interaction,
                                            error: app_commands.AppCommandError) -> bool:
    """
    Handles security-related errors for application commands.
    
    Args:
        interaction (discord.Interaction): The interaction that triggered the error.
        error (app_commands.AppCommandError): The error that occurred.
        
    Returns:
        bool: True if the error was handled, False otherwise.
    """
    if not isinstance(error, InsufficientLevelError):
        return False

    command_name = interaction.command.qualified_name if interaction.command else "unknown"
    log.warning("[SECURITY] Access Denied: User %s tried %s. Required: %s", interaction.user.id, command_name,
                error.required_roles)

    # Log the failure to the database for audited commands
    try:
        with SecurityInteractionRepository() as repo:
            repo.log_interaction(
                discord_id=interaction.user.id,
                command_name=command_name,
                event_type="FAILURE",
                details=f"Access Denied: Missing {error.required_roles}"
            )
    except Exception as e:
        log.error("Failed to log security failure to DB: %s", e)

    embed = error_embed(
        title="Permission Denied",
        description="You do not have the required permissions to use this command.",
        footer=True
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException as e:
        log.error("Failed to send security error message: %s", e)

    return True


async def handle_text_command_security_error(ctx: commands.Context, error: commands.CommandError) -> bool:
    """
    Handles security-related errors for text-based commands.
    
    Args:
        ctx (commands.Context): The context that triggered the error.
        error (commands.CommandError): The error that occurred.
        
    Returns:
        bool: True if the error was handled, False otherwise.
    """
    if not isinstance(error, InsufficientLevelError):
        return False

    command_name = ctx.command.qualified_name if ctx.command else "unknown"
    log.warning("[SECURITY] Access Denied: User %s tried %s. Required: %s", ctx.author.id, command_name,
                error.required_roles)

    # Log the failure to the database for audited commands
    try:
        with SecurityInteractionRepository() as repo:
            repo.log_interaction(
                discord_id=ctx.author.id,
                command_name=command_name,
                event_type="FAILURE",
                details=f"Access Denied: Missing {error.required_roles}"
            )
    except Exception as e:
        log.error("Failed to log security failure to DB: %s", e)

    embed = error_embed(
        title="Permission Denied",
        description="You do not have the required permissions to use this command.",
        footer=True
    )

    try:
        await ctx.reply(embed=embed, mention_author=False)
    except discord.HTTPException as e:
        log.error("Failed to send security error message: %s", e)

    return True
