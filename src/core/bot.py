from __future__ import annotations

import asyncio
import functools
from logging import getLogger
from typing import Optional

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import CommandNotFound

from src.cogs import EXTENSIONS
from src.config.main_server import ENVIRONMENT, GUILD_ID, get_bot_log_channel_id
from src.core.command_cooldowns import (
    apply_configured_cooldowns,
    handle_app_command_cooldown_error,
    handle_text_command_cooldown_error,
)
from src.data import BotInteractionType
from src.data.repository.auditlog_repository import AuditLogRepository
from src.utils.discord_utils import EngineerAlertField, send_engineer_log
from src.utils.embeds import AlertSeverity

log= getLogger(__name__)
import discord

__all__ = (
    "Bot",
)

def create_low_priority_task(func):
    async def wrapper(*args, **kwargs):
        try:
            await asyncio.to_thread(functools.partial(func, *args, **kwargs))
        except Exception as e:
            log.error(f"Error in low priority task: {e}")

    return lambda *args, **kwargs: asyncio.create_task(wrapper(*args, **kwargs), name=f"low_priority_task_{func.__name__}")

class Bot(discord.ext.commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
        )
        self._startup_log_sent = False

    async def on_ready(self) -> None:
        guild = self.get_guild(GUILD_ID)
        log.info("logged in as %s", self.user)
        log.info(
            "[STARTUP] Environment=%s Guild=%s BotLogChannel=%s",
            ENVIRONMENT,
            f"{guild.name} ({guild.id})" if guild is not None else f"Unavailable ({GUILD_ID})",
            get_bot_log_channel_id(),
        )
        if self._startup_log_sent:
            return

        try:
            await send_engineer_log(
                self,
                severity=AlertSeverity.INFO,
                title="Bot Startup",
                description="Paul connected and completed startup.",
                fields=_build_startup_log_fields(guild_name=guild.name if guild else None),
                notify_engineers=False,
            )
            self._startup_log_sent = True
        except Exception:
            log.error("Failed to send startup summary to bot log channel.", exc_info=True)
    '''
        try:
            spd_guild = self.get_guild(SPD_ID)
            if spd_guild:
                engine_room_channel = spd_guild.get_channel(ENGINE_ROOM)
                if engine_room_channel:
                    await engine_room_channel.send("I'm back from LOA")
                else:
                    log.error(f"Error: Channel with ID {ENGINE_ROOM} not found in SPD Guild.")
            else:
                log.error(f"Error: Guild with ID {SPD_ID} not found.")
        except Exception as e:
            log.error(f"Error: Startup Engine room error: {e}")
    '''

    async def success(self, content: str, interaction: discord.Interaction, ephemeral: Optional[bool]):
        """Sending success Message"""
        pass
    async def   error(self, content: str, interaction: discord.Interaction, ephemeral: Optional[bool]):
        """Sending error Message"""
        pass

    async def on_command(self, context: commands.Context):
        try:
            # Await the command
            audit_log_repository = AuditLogRepository()
            log.info(f"[COMMAND] [{context.message.id}] Received Command:")
            log.info(f"[COMMAND] [{context.message.id}] > Guild: {context.guild or 'None'}")
            log.info(f"[COMMAND] [{context.message.id}] > Channel: {context.channel or 'None'}")
            log.info(f"[COMMAND] [{context.message.id}] > User: {context.author or 'None'}")
            log.info(f"[COMMAND] [{context.message.id}] > Command: {context.command or 'None'}")
            log.info(f"[COMMAND] [{context.message.id}] > Arguments: {context.args or 'None'}")
            create_low_priority_task(audit_log_repository.log_interaction)(
                interaction_type=BotInteractionType.COMMAND,
                guild_id=context.guild.id,
                channel_id=context.channel.id,
                user_id=context.author.id,
                command_name=context.command or 'None',
                failed=context.command_failed
            )
        except CommandNotFound:
            pass

    async def on_command_error(
            self,
            context: commands.Context,
            error: commands.CommandError,
    ) -> None:
        if context.command is not None and context.command.has_error_handler():
            return

        if context.cog is not None and context.cog.has_error_handler():
            return

        if isinstance(error, CommandNotFound):
            return

        if await handle_text_command_cooldown_error(context, error):
            return

    async def on_app_command_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
    ) -> None:
        if await handle_app_command_cooldown_error(interaction, error):
            return

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            audit_log_repository = AuditLogRepository()
            log.info(f"[INTERACTION] [{interaction.id}] Received Interaction:")
            log.info(f"[INTERACTION] [{interaction.id}] > Guild: {interaction.guild or 'None'}")
            log.info(f"[INTERACTION] [{interaction.id}] > Channel: {interaction.channel or 'None'}")
            log.info(f"[INTERACTION] [{interaction.id}] > User: {interaction.user or 'None'}")

            log.info(f"[INTERACTION] [{interaction.id}] > Command: {interaction.data['name'] or 'None'}")
            log.info(f"[INTERACTION] [{interaction.id}] > > Options: {interaction.data.get('options', [])}")
            create_low_priority_task(audit_log_repository.log_interaction)(
                interaction_type=BotInteractionType.INTERACTION,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                user_id=interaction.user.id,
                command_name=str(interaction.data['name']) or 'None',
                failed=interaction.command_failed
            )


    async def setup_hook(self):
        log.info(f"Loading {len(EXTENSIONS)} extensions")
        for extension in EXTENSIONS:
            log.info(f"Loading {extension}")
            await self.load_extension(extension)
        apply_configured_cooldowns(self)
        self.tree.on_error = self.on_app_command_error
        log.info("All extentions loaded")
        # await self.tree.sync()
        log.info("Tree Synced")


def _build_startup_log_fields(*, guild_name: str | None) -> tuple[EngineerAlertField, ...]:
    guild_label = guild_name or f"Unavailable ({GUILD_ID})"
    return (
        EngineerAlertField("Environment", f"`{ENVIRONMENT}`"),
        EngineerAlertField("Guild", guild_label),
        EngineerAlertField("Extensions", f"`{len(EXTENSIONS)}`"),
        EngineerAlertField("Bot Log Channel", f"`{get_bot_log_channel_id()}`"),
    )
