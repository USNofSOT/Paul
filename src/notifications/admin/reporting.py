from __future__ import annotations

from datetime import datetime, time

import discord
from discord.utils import escape_markdown, escape_mentions

from src.config.notifications import (
    NOTIFICATION_DELIVERY_GRACE_HOURS,
    NOTIFICATION_LOOKAHEAD_HOURS,
    NotificationRolloutMap,
)
from src.config.task_timing import (
    CHECK_AWARDS_TASK_TIME,
    CHECK_TRAINING_AWARDS_TASK_TIME,
    COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS,
    COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS,
    COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS,
    TRACK_SHIP_SIZE_TASK_TIME,
)
from src.data.models import NotificationEvent
from src.notifications.types import NotificationDefinition, NotificationStatus, NotificationType
from src.utils.embeds import default_embed
from src.utils.emoji_utils import render_ship_label
from src.utils.ship_utils import get_ship_by_role_id


def _safe_text(value: str) -> str:
    return escape_mentions(escape_markdown(value))


def _format_clock(value: time) -> str:
    return value.strftime("%H:%M UTC")


def _format_interval_window(minimum_hours: int, maximum_hours: int) -> str:
    return f"every {minimum_hours}-{maximum_hours}h (jittered)"


def _format_relative(value: datetime | None) -> str:
    if value is None:
        return "Never"
    return f"<t:{int(value.timestamp())}:R>"


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "N/A"
    return f"<t:{int(value.timestamp())}:f>"


def _format_offsets(offsets: tuple[int, ...]) -> str:
    return ", ".join(str(offset) for offset in offsets)


def _ship_scope_label(ship_role_id: int, squad_role_ids: tuple[int, ...]) -> str:
    ship = get_ship_by_role_id(ship_role_id)
    ship_name = _safe_text(ship.name) if ship else f"Role {ship_role_id}"
    if not squad_role_ids:
        return ship_name
    return f"{ship_name} (squads: {', '.join(str(role_id) for role_id in squad_role_ids)})"


def summarize_rollout_scope(
        rollout_map: NotificationRolloutMap,
        notification_type: NotificationType,
) -> str:
    scoped_ships = rollout_map.get(notification_type, {})
    if not scoped_ships:
        return "Disabled"
    return "\n".join(
        f"- {_ship_scope_label(ship_role_id, squad_role_ids)}"
        for ship_role_id, squad_role_ids in scoped_ships.items()
    )


def build_notification_overview_embed(
        definitions: tuple[NotificationDefinition, ...],
        status_counts: dict[str, int],
        recent_events: list[NotificationEvent],
) -> discord.Embed:
    embed = default_embed(
        title="Notification Ops",
        description="Command inactivity reminders and queue health.",
        author=False,
    )
    embed.add_field(
        name="Task Timing",
        value=(
            f"Ship size: **{_format_clock(TRACK_SHIP_SIZE_TASK_TIME)}**\n"
            f"Notifications evaluator: **{_format_interval_window(COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS, COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS)}**\n"
            f"Worker poll: **every {COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS}s**\n"
            f"Projection: **{NOTIFICATION_LOOKAHEAD_HOURS}h lookahead**, **{NOTIFICATION_DELIVERY_GRACE_HOURS}h grace**\n"
            f"Awards: **{_format_clock(CHECK_AWARDS_TASK_TIME)}**\n"
            f"Training awards: **{_format_clock(CHECK_TRAINING_AWARDS_TASK_TIME)}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="Definitions",
        value="\n".join(
            f"`{definition.notification_type.value}`: "
            f"{definition.threshold_days} days, offsets [{_format_offsets(definition.trigger_offsets)}]"
            for definition in definitions
        ),
        inline=False,
    )
    embed.add_field(
        name="Queue Status",
        value="\n".join(
            f"{status.value.title()}: **{status_counts.get(status.value, 0)}**"
            for status in NotificationStatus
        ),
        inline=False,
    )
    if recent_events:
        embed.add_field(
            name="Recent Events",
            value="\n".join(_format_event_line(event) for event in recent_events[:5]),
            inline=False,
        )
    return embed


def build_notification_definitions_embed(
        definitions: tuple[NotificationDefinition, ...],
        rollout_map: NotificationRolloutMap,
) -> discord.Embed:
    embed = default_embed(
        title="Notification Definitions",
        description="Configured reminder definitions and rollout scope.",
        author=False,
    )
    for definition in definitions:
        embed.add_field(
            name=definition.notification_type.value,
            value=(
                f"Activity: **{definition.activity_field}**\n"
                f"Threshold: **{definition.threshold_days} days**\n"
                f"Offsets: **[{_format_offsets(definition.trigger_offsets)}]**\n"
                f"Route: **{definition.routing_target.value}**\n"
                f"Rollout:\n{summarize_rollout_scope(rollout_map, definition.notification_type)}"
            ),
            inline=False,
        )
    return embed


def _format_event_line(event: NotificationEvent) -> str:
    return (
        f"`#{event.id}` {render_ship_label(ship_role_id=event.ship_role_id)} "
        f"`{event.notification_type}` `{event.status}` sailor={event.sailor_id} "
        f"offset={event.trigger_offset} scheduled={_format_timestamp(event.scheduled_for_at)} "
        f"threshold={_format_timestamp(event.threshold_at)} created={_format_relative(event.created_at)}"
    )


def build_notification_recent_events_embed(
        events: list[NotificationEvent],
) -> discord.Embed:
    embed = default_embed(
        title="Recent Notification Events",
        description="Newest command inactivity notification events.",
        author=False,
    )
    embed.description = (
        "\n".join(_format_event_line(event) for event in events)
        if events
        else "No notification events recorded yet."
    )
    return embed


def build_notification_action_embed(title: str, description: str) -> discord.Embed:
    return default_embed(
        title=_safe_text(title),
        description=_safe_text(description),
        author=False,
    )
