from __future__ import annotations

import re
from collections.abc import Iterable
from logging import getLogger
from math import ceil

import discord
from discord import app_commands
from discord.ext import commands

from src.config.cooldowns import (
    CommandCooldownConfig,
    get_command_cooldown_config,
)
from src.utils.embeds import error_embed

COOLDOWN_TRACKING_KEY = "cooldown_message"
COOLDOWN_SECONDS_KEY = "cooldown_seconds"
COOLDOWN_APPLIED_KEY = "_configured_cooldown_applied"
COMMAND_NAME_MAX_LENGTH = 64
COOLDOWN_MESSAGE_MAX_LENGTH = 512
_INVALID_COMMAND_NAME_CHARACTERS = re.compile(r"[^a-z0-9_\- ]+")

log = getLogger(__name__)


def _command_name(command: app_commands.Command | commands.Command) -> str:
    qualified_name = getattr(command, "qualified_name", None)
    if qualified_name:
        return qualified_name.lower()
    return command.name.lower()


def normalize_command_name(command_name: str) -> str:
    normalized_command_name = _INVALID_COMMAND_NAME_CHARACTERS.sub(
        "_",
        command_name.lower().strip(),
    )
    normalized_command_name = " ".join(normalized_command_name.split())
    if not normalized_command_name:
        return "unknown"
    return normalized_command_name[:COMMAND_NAME_MAX_LENGTH]


def sanitize_cooldown_text(
        value: str | None,
        *,
        limit: int = COOLDOWN_MESSAGE_MAX_LENGTH,
        escape_markdown: bool = False,
) -> str:
    sanitized_value = (value or "").replace("\x00", "").strip()
    sanitized_value = sanitized_value.replace("@", "@\u200b")
    if escape_markdown:
        sanitized_value = discord.utils.escape_markdown(sanitized_value)
    if len(sanitized_value) <= limit:
        return sanitized_value
    return f"{sanitized_value[: limit - 3]}..."


def apply_configured_cooldowns(bot: commands.Bot) -> None:
    _apply_app_command_cooldowns(bot.tree.walk_commands())
    _apply_text_command_cooldowns(bot.walk_commands())


def _apply_app_command_cooldowns(
        app_command_items: Iterable[app_commands.Command],
) -> None:
    for command in app_command_items:
        spec = get_command_cooldown_config(_command_name(command))
        command.extras[COOLDOWN_SECONDS_KEY] = spec.seconds
        command.extras[COOLDOWN_TRACKING_KEY] = spec.message

        if command.extras.get(COOLDOWN_APPLIED_KEY) or spec.seconds == 0:
            command.extras[COOLDOWN_APPLIED_KEY] = True
            continue

        app_commands.checks.cooldown(1, spec.seconds)(command)
        command.extras[COOLDOWN_APPLIED_KEY] = True


def _apply_text_command_cooldowns(
        text_commands: Iterable[commands.Command],
) -> None:
    for command in text_commands:
        spec = get_command_cooldown_config(_command_name(command))
        command.extras[COOLDOWN_SECONDS_KEY] = spec.seconds
        command.extras[COOLDOWN_TRACKING_KEY] = spec.message

        if command.extras.get(COOLDOWN_APPLIED_KEY) or spec.seconds == 0:
            command.extras[COOLDOWN_APPLIED_KEY] = True
            continue

        commands.cooldown(1, spec.seconds, commands.BucketType.user)(command)
        command.extras[COOLDOWN_APPLIED_KEY] = True


def format_cooldown_message(
        command_name: str,
        retry_after: float,
        spec: CommandCooldownConfig | None = None,
) -> str:
    normalized_command_name = normalize_command_name(command_name)
    spec = spec or get_command_cooldown_config(command_name)
    retry_after_seconds = max(1, ceil(retry_after))

    try:
        return sanitize_cooldown_text(
            spec.message.format(
                command_name=normalized_command_name,
                retry_after=retry_after_seconds,
                retry_after_seconds=retry_after_seconds,
                cooldown_seconds=spec.seconds,
            )
        )
    except (IndexError, KeyError, ValueError):
        return sanitize_cooldown_text(
            (
                "Please wait "
                f"{retry_after_seconds} seconds before using "
                f"`{normalized_command_name}` again."
            )
        )


def build_cooldown_error_embed(
        command_name: str,
        retry_after: float,
        spec: CommandCooldownConfig | None = None,
) -> discord.Embed:
    description = format_cooldown_message(command_name, retry_after, spec)
    return error_embed(
        title="Command on cooldown",
        description=description,
        footer=False,
    )


def build_cooldown_stats_payload(
        command_name: str,
        retry_after: float,
        spec: CommandCooldownConfig | None = None,
) -> dict[str, str | int]:
    normalized_command_name = normalize_command_name(command_name)
    spec = spec or get_command_cooldown_config(normalized_command_name)
    retry_after_seconds = max(1, ceil(retry_after))
    rendered_message = format_cooldown_message(
        normalized_command_name,
        retry_after_seconds,
        spec,
    )

    return {
        "command_name": normalized_command_name,
        "cooldown_seconds": max(0, spec.seconds),
        "retry_after_seconds": retry_after_seconds,
        "rendered_message": rendered_message,
    }


def record_command_cooldown_event(
        command_name: str,
        retry_after: float,
        spec: CommandCooldownConfig | None = None,
) -> str:
    payload = build_cooldown_stats_payload(command_name, retry_after, spec)

    try:
        from src.data.repository.command_cooldown_stats_repository import (
            CommandCooldownStatsRepository,
        )

        repository = CommandCooldownStatsRepository()
        try:
            repository.record_cooldown(
                payload["command_name"],
                cooldown_seconds=payload["cooldown_seconds"],
                retry_after_seconds=payload["retry_after_seconds"],
            )
        finally:
            repository.close_session()
    except Exception as e:
        log.error(
            "Failed to record cooldown event for %s: %s",
            payload["command_name"],
            e,
        )

    return payload["rendered_message"]


async def send_interaction_error(
        interaction: discord.Interaction,
        *,
        embed: discord.Embed,
        ephemeral: bool = True,
) -> None:
    allowed_mentions = discord.AllowedMentions.none()
    if interaction.response.is_done():
        await interaction.followup.send(
            embed=embed,
            ephemeral=ephemeral,
            allowed_mentions=allowed_mentions,
        )
        return

    await interaction.response.send_message(
        embed=embed,
        ephemeral=ephemeral,
        allowed_mentions=allowed_mentions,
    )


async def handle_app_command_cooldown_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
) -> bool:
    if not isinstance(error, app_commands.errors.CommandOnCooldown):
        return False

    command_name = (
        interaction.command.qualified_name
        if interaction.command is not None
        else "unknown"
    )
    description = record_command_cooldown_event(command_name, error.retry_after)
    embed = error_embed(
        title="Command on cooldown",
        description=description,
        footer=False,
    )
    await send_interaction_error(interaction, embed=embed, ephemeral=True)
    return True


async def handle_text_command_cooldown_error(
        context: commands.Context,
        error: commands.CommandError,
) -> bool:
    if not isinstance(error, commands.CommandOnCooldown):
        return False

    command_name = context.command.qualified_name if context.command else "unknown"
    description = record_command_cooldown_event(command_name, error.retry_after)
    embed = error_embed(
        title="Command on cooldown",
        description=description,
        footer=False,
    )
    await context.reply(
        embed=embed,
        mention_author=False,
        allowed_mentions=discord.AllowedMentions.none(),
    )
    return True
