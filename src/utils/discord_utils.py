from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from logging import getLogger
from typing import Protocol

import discord
from discord.ext import commands

from src.config import ENGINEERS
from src.config.main_server import GUILD_ID, get_bot_log_channel_id
from src.utils.embeds import AlertSeverity, engineer_alert_embed

log = getLogger(__name__)


@dataclass(frozen=True)
class EngineerAlertField:
    label: str
    value: str


@dataclass(frozen=True)
class EngineerAlert:
    severity: AlertSeverity
    title: str
    description: str
    exception: Exception | None = None
    fields: tuple[EngineerAlertField, ...] = field(default_factory=tuple)
    notify_engineers: bool = True
    guild_id: int = GUILD_ID
    channel_id: int = field(default_factory=get_bot_log_channel_id)


class EngineerAlertDispatcher(Protocol):
    async def dispatch(self, bot: commands.Bot, alert: EngineerAlert) -> None: ...


class DiscordEngineerAlertDispatcher:
    async def dispatch(self, bot: commands.Bot, alert: EngineerAlert) -> None:
        embed = engineer_alert_embed(
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            exception=alert.exception,
            fields=tuple((field.label, field.value) for field in alert.fields),
        )
        embed.timestamp = datetime.now(UTC)

        guild = bot.get_guild(alert.guild_id)
        if guild is None:
            log.warning(
                "Engineer alert skipped guild delivery because guild %s could not be resolved.",
                alert.guild_id,
            )
            return

        if alert.notify_engineers:
            await self._send_engineer_dms(guild, embed)

        await self._send_channel_message(guild, alert.channel_id, embed)

    async def _send_engineer_dms(
            self, guild: discord.Guild, embed: discord.Embed
    ) -> None:
        for engineer_id in ENGINEERS:
            engineer = guild.get_member(engineer_id)
            if engineer is None:
                log.warning(
                    "Engineer alert skipped DM because engineer %s is not in guild %s.",
                    engineer_id,
                    guild.id,
                )
                continue

            try:
                await engineer.send(embed=embed)
            except discord.HTTPException:
                log.error("Error sending alert to engineer %s", engineer_id)

    async def _send_channel_message(
            self, guild: discord.Guild, channel_id: int, embed: discord.Embed
    ) -> None:
        channel = guild.get_channel(channel_id)
        if channel is None:
            log.warning(
                "Engineer alert skipped channel delivery because channel %s could not be resolved.",
                channel_id,
            )
            return

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            log.error("Error sending alert to channel %s", channel_id)


DEFAULT_ENGINEER_ALERT_DISPATCHER = DiscordEngineerAlertDispatcher()


async def send_engineer_alert(
        bot: commands.Bot,
        alert: EngineerAlert,
        *,
        dispatcher: EngineerAlertDispatcher = DEFAULT_ENGINEER_ALERT_DISPATCHER,
) -> None:
    await dispatcher.dispatch(bot, alert)


async def send_engineer_log(
        bot: commands.Bot,
        *,
        severity: AlertSeverity,
        title: str,
        description: str,
        exception: Exception | None = None,
        fields: tuple[EngineerAlertField, ...] = (),
        notify_engineers: bool = False,
        channel_id: int | None = None,
        guild_id: int = GUILD_ID,
        dispatcher: EngineerAlertDispatcher = DEFAULT_ENGINEER_ALERT_DISPATCHER,
) -> None:
    await send_engineer_alert(
        bot,
        EngineerAlert(
            severity=severity,
            title=title,
            description=description,
            exception=exception,
            fields=fields,
            notify_engineers=notify_engineers,
            guild_id=guild_id,
            channel_id=channel_id if channel_id is not None else get_bot_log_channel_id(),
        ),
        dispatcher=dispatcher,
    )


async def alert_engineers(
        bot: commands.Bot,
        message: str,
        exception: Exception = None,
        *,
        title: str = "Unexpected Error Occurred",
        fields: tuple[EngineerAlertField, ...] = (),
        dispatcher: EngineerAlertDispatcher = DEFAULT_ENGINEER_ALERT_DISPATCHER,
) -> None:
    await send_engineer_alert(
        bot,
        EngineerAlert(
            severity=AlertSeverity.ERROR,
            title=title,
            description=message,
            exception=exception,
            fields=fields,
            notify_engineers=True,
        ),
        dispatcher=dispatcher,
    )


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
        if guild is None:
            return f"Unknown ({discord_id})"
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
