from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

import discord
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from discord.ext import commands

from src.config.cache import IMAGE_CACHES
from src.config.main_server import GUILD_ID
from src.config.notifications import (
    SHIP_HEALTH_SUMMARY_ENABLED,
    SHIP_HEALTH_SUMMARY_HOSTING_DUE_SOON_DAYS,
    SHIP_HEALTH_SUMMARY_RECENT_ACTIVITY_DAYS,
    SHIP_HEALTH_SUMMARY_ROLLOUT,
    SHIP_HEALTH_SUMMARY_VOYAGE_DUE_SOON_DAYS,
    ShipHealthSummaryRollout,
)
from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.config.ships import SHIPS
from src.notifications.context import get_squad_role
from src.notifications.contracts import (
    NotificationDeliveryAdapter,
    NotificationRouteResolver,
    ShipHealthSummaryDataProvider,
    ShipHealthSummaryRenderer,
)
from src.notifications.date_utils import ensure_utc
from src.notifications.types import (
    NotificationField,
    RenderedNotification,
    ShipHealthSummary,
    ShipHealthSummaryRunSummary,
)
from src.utils.emoji_utils import resolve_ship_emoji
from src.utils.embeds import default_embed

log = logging.getLogger(__name__)


class DatabaseShipHealthSummaryDataProvider:
    def __init__(
            self,
            repository,
            *,
            recent_activity_days: int = SHIP_HEALTH_SUMMARY_RECENT_ACTIVITY_DAYS,
            voyage_due_soon_days: int = SHIP_HEALTH_SUMMARY_VOYAGE_DUE_SOON_DAYS,
            hosting_due_soon_days: int = SHIP_HEALTH_SUMMARY_HOSTING_DUE_SOON_DAYS,
    ) -> None:
        self.repository = repository
        self.recent_activity_days = recent_activity_days
        self.voyage_due_soon_days = voyage_due_soon_days
        self.hosting_due_soon_days = hosting_due_soon_days

    def build_summary(
            self,
            *,
            ship_role_id: int,
            ship_name: str,
            ship_size: int,
            sailor_ids: list[int],
            reference_time: datetime,
    ) -> ShipHealthSummary:
        resolved_reference_time = ensure_utc(reference_time)
        sailors = self.repository.get_sailors_by_ids(sailor_ids)
        recent_window_start = resolved_reference_time - timedelta(days=self.recent_activity_days)
        previous_window_start = recent_window_start - timedelta(days=self.recent_activity_days)
        previous_ship_size = self.repository.get_ship_size_on_or_before(
            ship_role_id=ship_role_id,
            before=recent_window_start,
        )
        current_voyage_count = self.repository.count_voyage_logs_between(
            ship_role_id=ship_role_id,
            start=recent_window_start,
            end=resolved_reference_time,
        )
        previous_voyage_count = self.repository.count_voyage_logs_between(
            ship_role_id=ship_role_id,
            start=previous_window_start,
            end=recent_window_start,
        )
        current_hosting_count = self.repository.count_hosting_logs_between(
            ship_role_id=ship_role_id,
            start=recent_window_start,
            end=resolved_reference_time,
        )
        previous_hosting_count = self.repository.count_hosting_logs_between(
            ship_role_id=ship_role_id,
            start=previous_window_start,
            end=recent_window_start,
        )

        return ShipHealthSummary(
            ship_role_id=ship_role_id,
            ship_name=ship_name,
            ship_size=ship_size,
            ship_size_delta=ship_size - previous_ship_size if previous_ship_size is not None else 0,
            voyaging_due_soon_count=self._count_due_soon(
                sailors=sailors,
                activity_field="last_voyage_at",
                threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
                due_soon_days=self.voyage_due_soon_days,
                reference_time=resolved_reference_time,
            ),
            voyaging_overdue_count=self._count_overdue(
                sailors=sailors,
                activity_field="last_voyage_at",
                threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
                reference_time=resolved_reference_time,
            ),
            hosting_due_soon_count=self._count_due_soon(
                sailors=sailors,
                activity_field="last_hosting_at",
                threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
                due_soon_days=self.hosting_due_soon_days,
                reference_time=resolved_reference_time,
            ),
            hosting_overdue_count=self._count_overdue(
                sailors=sailors,
                activity_field="last_hosting_at",
                threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
                reference_time=resolved_reference_time,
            ),
            recent_voyage_count=current_voyage_count,
            recent_voyage_delta=current_voyage_count - previous_voyage_count,
            recent_hosting_count=current_hosting_count,
            recent_hosting_delta=current_hosting_count - previous_hosting_count,
            recent_activity_days=self.recent_activity_days,
        )

    @staticmethod
    def _resolve_threshold_at(
            activity_at: datetime | None,
            *,
            threshold_days: int,
    ) -> datetime | None:
        if activity_at is None:
            return None
        return ensure_utc(activity_at) + timedelta(days=threshold_days)

    def _count_due_soon(
            self,
            *,
            sailors,
            activity_field: str,
            threshold_days: int,
            due_soon_days: int,
            reference_time: datetime,
    ) -> int:
        due_window_end = reference_time + timedelta(days=due_soon_days)
        count = 0
        for sailor in sailors:
            threshold_at = self._resolve_threshold_at(
                getattr(sailor, activity_field),
                threshold_days=threshold_days,
            )
            if threshold_at is None:
                continue
            if reference_time <= threshold_at <= due_window_end:
                count += 1
        return count

    def _count_overdue(
            self,
            *,
            sailors,
            activity_field: str,
            threshold_days: int,
            reference_time: datetime,
    ) -> int:
        count = 0
        for sailor in sailors:
            threshold_at = self._resolve_threshold_at(
                getattr(sailor, activity_field),
                threshold_days=threshold_days,
            )
            if threshold_at is None:
                continue
            if threshold_at < reference_time:
                count += 1
        return count


class ShipHealthSummaryEmbedRenderer:
    def render(self, summary: ShipHealthSummary) -> RenderedNotification:
        ship_emoji = resolve_ship_emoji(ship_role_id=summary.ship_role_id)
        chart_filename = IMAGE_CACHES["ship_health_summary_chart"].default_filename

        embed = default_embed(
            title=f"{ship_emoji} Ship health summary",
            description=f"Weekly operational overview for {summary.ship_name}.",
            author=False,
        )
        embed.color = discord.Color.blue()
        embed.add_field(
            name="👥 Crew",
            value=f"Members: **{self._format_metric(summary.ship_size, summary.ship_size_delta)}**",
            inline=False,
        )
        embed.add_field(
            name="⚓ Recent Activity",
            value=(
                f"Voyages ({summary.recent_activity_days}d): **{self._format_metric(summary.recent_voyage_count, summary.recent_voyage_delta)}**\n"
                f"Hosted ({summary.recent_activity_days}d): **{self._format_metric(summary.recent_hosting_count, summary.recent_hosting_delta)}**"
            ),
            inline=False,
        )

        chart_bytes = _get_or_create_ship_health_chart(
            {
                "chart_version": 3,
                "ship_role_id": summary.ship_role_id,
                "ship_size": summary.ship_size,
                "ship_size_delta": summary.ship_size_delta,
                "recent_voyage_count": summary.recent_voyage_count,
                "recent_voyage_delta": summary.recent_voyage_delta,
                "recent_hosting_count": summary.recent_hosting_count,
                "recent_hosting_delta": summary.recent_hosting_delta,
                "recent_activity_days": summary.recent_activity_days,
            },
            lambda: self._render_chart(summary),
        )

        return RenderedNotification(
            embed_title=embed.title or "",
            embed_description=embed.description or "",
            fields=tuple(
                NotificationField(
                    name=field.name,
                    value=field.value,
                    inline=field.inline,
                )
                for field in embed.fields
            ),
            footer=embed.footer.text or "",
            color_value=embed.color.value,
            image_attachment_filename=chart_filename if chart_bytes else None,
            image_attachment_bytes=chart_bytes,
        )

    @staticmethod
    def _format_metric(value: int, delta: int) -> str:
        sign = "+" if delta > 0 else ""
        return f"{value} ({sign}{delta})"

    def _render_chart(self, summary: ShipHealthSummary) -> bytes:
        current_values = [
            summary.ship_size,
            summary.recent_voyage_count,
            summary.recent_hosting_count,
        ]
        previous_values = [
            max(0, summary.ship_size - summary.ship_size_delta),
            max(0, summary.recent_voyage_count - summary.recent_voyage_delta),
            max(0, summary.recent_hosting_count - summary.recent_hosting_delta),
        ]
        labels = [
            "Members",
            "Voyages",
            "Hosted",
        ]

        return _render_summary_chart_png(
            current_values=current_values,
            previous_values=previous_values,
            labels=labels,
            title="This Week vs Previous",
        )


def _get_or_create_ship_health_chart(payload: dict[str, int], producer) -> bytes:
    config = IMAGE_CACHES["ship_health_summary_chart"]
    directory = Path(config.directory)
    directory.mkdir(parents=True, exist_ok=True)

    cache_key = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    path = directory / f"{cache_key}{config.extension}"

    if path.exists():
        return path.read_bytes()

    data = producer()
    path.write_bytes(data)
    return data


def _render_summary_chart_png(
        current_values: list[int],
        previous_values: list[int],
        labels: list[str],
        *,
        title: str = "This Week vs Previous",
) -> bytes:
    if not current_values and not previous_values and not labels:
        current = [0]
        previous = [0]
        resolved_labels = ["No data"]
    else:
        if not (len(current_values) == len(previous_values) == len(labels)):
            raise ValueError(
                "current_values, previous_values, and labels must have the same length"
            )
        current = [max(0, int(value)) for value in current_values]
        previous = [max(0, int(value)) for value in previous_values]
        resolved_labels = labels

    max_value = max(current + previous + [1])
    x_limit = max_value * 1.15

    row_count = len(resolved_labels)
    fig_height = max(2.8, 0.9 + row_count * 0.75)
    fig, ax = plt.subplots(figsize=(6.2, fig_height), dpi=110)

    fig.patch.set_facecolor("#f3f4f6")
    ax.set_facecolor("#f3f4f6")

    y_positions = list(range(row_count))
    bar_height = 0.36

    previous_y = [y - bar_height / 2 for y in y_positions]
    current_y = [y + bar_height / 2 for y in y_positions]

    ax.barh(
        previous_y,
        previous,
        height=bar_height,
        color="#94a3b8",
        label="Previous",
    )
    ax.barh(
        current_y,
        current,
        height=bar_height,
        color="#2563eb",
        label="Current",
    )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(resolved_labels, fontsize=11)
    ax.invert_yaxis()

    ax.set_title(title, fontsize=12)
    ax.set_xlim(0, x_limit)
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)

    # add value labels for previous week
    for y, value in zip(previous_y, previous):
        ax.text(
            value + max_value * 0.01,
            y,
            str(value),
            va="center",
            ha="left",
            fontsize=9,
            color="#374151",
        )

    # add value labels for current week
    for y, value in zip(current_y, current):
        ax.text(
            value + max_value * 0.01,
            y,
            str(value),
            va="center",
            ha="left",
            fontsize=9,
            color="#111827",
        )

    ax.legend(
        loc="lower right",
        frameon=False,
        fontsize=9,
        handlelength=1.6,
    )

    fig.tight_layout()

    output = BytesIO()
    fig.savefig(
        output,
        format="png",
        bbox_inches="tight",
        pad_inches=0.2,
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    return output.getvalue()


class ShipHealthSummaryService:
    def __init__(
            self,
            data_provider: ShipHealthSummaryDataProvider,
            renderer: ShipHealthSummaryRenderer,
            route_resolver: NotificationRouteResolver,
            delivery_adapter: NotificationDeliveryAdapter,
            *,
            enabled: bool = SHIP_HEALTH_SUMMARY_ENABLED,
            rollout: ShipHealthSummaryRollout = SHIP_HEALTH_SUMMARY_ROLLOUT,
    ) -> None:
        self.data_provider = data_provider
        self.renderer = renderer
        self.route_resolver = route_resolver
        self.delivery_adapter = delivery_adapter
        self.enabled = enabled
        self.rollout = set(rollout)

    async def run_once(
            self,
            bot: commands.Bot,
            reference_time: datetime | None = None,
    ) -> ShipHealthSummaryRunSummary:
        if not self.enabled:
            return ShipHealthSummaryRunSummary(summary_count=0)

        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning("Ship health summary skipped because the guild is unavailable.")
            return ShipHealthSummaryRunSummary(summary_count=0)

        resolved_reference_time = ensure_utc(reference_time or datetime.now(UTC))
        summary_count = 0
        skipped_count = 0
        per_ship_counts: defaultdict[int | None, int] = defaultdict(int)
        skipped_ship_counts: defaultdict[int | None, int] = defaultdict(int)

        for ship in SHIPS:
            if ship.role_id is None or ship.role_id not in self.rollout:
                continue

            role = guild.get_role(ship.role_id)
            if role is None:
                skipped_count += 1
                skipped_ship_counts[ship.role_id] += 1
                log.warning("Ship health summary skipped because role %s is unavailable.", ship.role_id)
                continue

            route = self.route_resolver.resolve_ship_role(ship.role_id, guild)
            if route.destination_channel_id is None:
                skipped_count += 1
                skipped_ship_counts[ship.role_id] += 1
                log.info(
                    "Ship health summary skipped for ship %s: %s",
                    ship.role_id,
                    route.skip_reason,
                )
                continue

            summary = self.data_provider.build_summary(
                ship_role_id=ship.role_id,
                ship_name=ship.name,
                ship_size=len(role.members),
                sailor_ids=[member.id for member in role.members],
                reference_time=resolved_reference_time,
            )
            rendered = self.renderer.render(summary)
            await self.delivery_adapter.send(
                guild,
                route.destination_channel_id,
                rendered,
            )
            summary_count += 1
            per_ship_counts[ship.role_id] += 1

        return ShipHealthSummaryRunSummary(
            summary_count=summary_count,
            skipped_count=skipped_count,
            per_ship_counts=dict(per_ship_counts),
            skipped_ship_counts=dict(skipped_ship_counts),
        )

    @staticmethod
    def _build_squad_memberships(members: list) -> dict[str, list[int]]:
        squads: defaultdict[str, list[int]] = defaultdict(list)
        for member in members:
            squad_role = get_squad_role(member)
            if squad_role is None:
                continue
            squads[squad_role.name].append(member.id)
        return dict(squads)
