from __future__ import annotations

import asyncio
import functools
import json
import time
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
from src.security.error_handler import (
    handle_app_command_security_error,
    handle_text_command_security_error,
)
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


_cmd_start_times: dict[int, float] = {}

from datetime import datetime, UTC

class Bot(discord.ext.commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
        )
        self.start_time = datetime.now(tz=UTC)
        self._startup_log_sent = False

    async def on_app_command_completion(
            self,
            interaction: discord.Interaction,
            command: app_commands.Command | app_commands.ContextMenu,
    ) -> None:
        start = _cmd_start_times.pop(interaction.id, None)
        if start is None:
            return
        elapsed_ms = (time.perf_counter() - start) * 1000
        interaction_id = interaction.id

        async def _record_after_insert():
            await asyncio.sleep(0.5)
            repo = AuditLogRepository()
            try:
                repo.record_execution_time(interaction_id, elapsed_ms)
            finally:
                repo.close_session()

        asyncio.create_task(_record_after_insert())

    async def dispatch_engineer_alert(self, alert: EngineerAlert):
        """Helper to dispatch engineer alerts asynchronously."""
        from src.utils.discord_utils import send_engineer_alert
        try:
            await send_engineer_alert(self, alert)
        except Exception as e:
            # Avoid recursion by using standard print
            print(f"Failed to dispatch engineer alert: {e}")

    async def on_ready(self) -> None:
        guild = self.get_guild(GUILD_ID)
        log.info("logged in as %s", self.user)
        log.info(
            "[STARTUP] Environment=%s Guild=%s BotLogChannel=%s",
            ENVIRONMENT,
            f"{guild.name} ({guild.id})" if guild is not None else f"Unavailable ({GUILD_ID})",
            get_bot_log_channel_id(),
        )

        # Process any logs that occurred before the bot was ready
        if hasattr(self, "_early_logs") and self._early_logs:
            for alert in self._early_logs:
                self.loop.create_task(self.dispatch_engineer_alert(alert))
            self._early_logs.clear()

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

            # Serialize arguments for logging
            args_str = None
            try:
                args_str = json.dumps({
                    "args": [str(a) for a in context.args],
                    "kwargs": {k: str(v) for k, v in context.kwargs.items()},
                    "content": context.message.content
                })
            except Exception as e:
                log.warning(f"Failed to serialize command arguments: {e}")
                args_str = str(context.args)

            log.info(f"[COMMAND] [{context.message.id}] > Arguments: {args_str}")
            
            create_low_priority_task(audit_log_repository.log_interaction)(
                interaction_type=BotInteractionType.COMMAND,
                guild_id=context.guild.id,
                channel_id=context.channel.id,
                user_id=context.author.id,
                command_name=context.command.name if context.command else 'None',
                failed=context.command_failed,
                interaction_id=context.message.id,
                args=args_str
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

        if await handle_text_command_security_error(context, error):
            return

        # Record error in audit log
        try:
            audit_log_repository = AuditLogRepository()
            audit_log_repository.record_error(interaction_id=context.message.id, error_message=str(error))
        except Exception as e:
            log.error(f"Failed to record command error in audit log: {e}")

        log.error(
            "Command error in %s: %s",
            context.command,
            error,
            extra={
                "notify_engineer": True,
                "user_id": context.author.id,
                "command_name": context.command.name if context.command else "Unknown",
                "channel_id": context.channel.id if context.channel else None
            }
        )

    async def on_app_command_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
    ) -> None:
        start = _cmd_start_times.pop(interaction.id, None)
        if start is not None:
            elapsed_ms = (time.perf_counter() - start) * 1000
            interaction_id = interaction.id

            async def _record_after_insert():
                await asyncio.sleep(0.5)
                repo = AuditLogRepository()
                try:
                    repo.record_execution_time(interaction_id, elapsed_ms)
                finally:
                    repo.close_session()

            asyncio.create_task(_record_after_insert())

        if await handle_app_command_cooldown_error(interaction, error):
            return
        if await handle_app_command_security_error(interaction, error):
            return

        # Record error in audit log
        try:
            audit_log_repository = AuditLogRepository()
            audit_log_repository.record_error(interaction_id=interaction.id, error_message=str(error))
        except Exception as e:
            log.error(f"Failed to record app command error in audit log: {e}")

        log.error(
            "App command error: %s",
            error,
            extra={
                "notify_engineer": True,
                "user_id": interaction.user.id,
                "command_name": interaction.command.name if interaction.command else "Unknown",
                "channel_id": interaction.channel.id if interaction.channel else None
            }
        )

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            _cmd_start_times[interaction.id] = time.perf_counter()
            audit_log_repository = AuditLogRepository()
            log.info(f"[INTERACTION] [{interaction.id}] Received Interaction:")
            log.info(f"[INTERACTION] [{interaction.id}] > Guild: {interaction.guild or 'None'}")
            log.info(f"[INTERACTION] [{interaction.id}] > Channel: {interaction.channel or 'None'}")
            log.info(f"[INTERACTION] [{interaction.id}] > User: {interaction.user or 'None'}")

            log.info(f"[INTERACTION] [{interaction.id}] > Command: {interaction.data.get('name', 'None')}")

            # Serialize options for logging
            options = interaction.data.get('options', [])
            args_str = None
            try:
                args_str = json.dumps(options)
            except Exception as e:
                log.warning(f"Failed to serialize interaction options: {e}")
                args_str = str(options)

            log.info(f"[INTERACTION] [{interaction.id}] > > Options: {args_str}")
            
            create_low_priority_task(audit_log_repository.log_interaction)(
                interaction_type=BotInteractionType.INTERACTION,
                guild_id=interaction.guild.id if interaction.guild else 0,
                channel_id=interaction.channel.id if interaction.channel else 0,
                user_id=interaction.user.id,
                command_name=str(interaction.data.get('name', 'Unknown')),
                failed=interaction.command_failed,
                interaction_id=interaction.id,
                args=args_str
            )


    async def setup_hook(self):
        # Register the notification callback for instant engineer alerts
        import logging
        import traceback
        from src.utils.logger import set_notification_callback
        from src.utils.discord_utils import EngineerAlert, AlertSeverity

        self._early_logs = []

        def notification_callback(record: logging.LogRecord):
            # Map logging levels to AlertSeverity
            severity_map = {
                logging.DEBUG: AlertSeverity.INFO,
                logging.INFO: AlertSeverity.INFO,
                logging.WARNING: AlertSeverity.WARNING,
                logging.ERROR: AlertSeverity.ERROR,
                logging.CRITICAL: AlertSeverity.CRITICAL,
            }
            severity = severity_map.get(record.levelno, AlertSeverity.ERROR)

            # Extract exception and stack trace
            exc_info = record.exc_info
            stack_trace = None
            exception = None
            if exc_info:
                exception = exc_info[1]
                stack_trace = "".join(traceback.format_exception(*exc_info))

            # Extract human context from 'extra' fields
            fields = []
            user_id = getattr(record, "user_id", None)
            if user_id:
                from src.utils.discord_utils import get_best_display_name
                user_display = get_best_display_name(self, user_id)
                fields.append(EngineerAlertField("User", f"{user_display} (<@{user_id}>)"))

            command_name = getattr(record, "command_name", None)
            if command_name:
                fields.append(EngineerAlertField("Command", f"`/{command_name}`"))

            channel_id = getattr(record, "channel_id", None)
            if channel_id:
                fields.append(EngineerAlertField("Channel", f"<#{channel_id}>"))

            from datetime import datetime
            log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

            alert = EngineerAlert(
                severity=severity,
                title=f"Log {record.levelname}: {record.name}",
                description=record.getMessage(),
                logger_name=record.name,
                exception=exception,
                stack_trace=stack_trace,
                fields=tuple(fields),
                notify_engineers=True,
                log_time=log_time,
            )

            if self.is_ready():
                self.loop.create_task(
                    self.dispatch_engineer_alert(alert)
                )
            else:
                self._early_logs.append(alert)

        set_notification_callback(notification_callback)

        log.info(f"Loading {len(EXTENSIONS)} extensions")
        for extension in EXTENSIONS:
            log.info(f"Loading {extension}")
            await self.load_extension(extension)
        apply_configured_cooldowns(self)
        self.tree.on_error = self.on_app_command_error
        self.tree.on_completion = self.on_app_command_completion
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
