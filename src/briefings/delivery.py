from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

import discord
from discord.ext import commands

from src.briefings.daily import (
    DailyShipBriefing,
    build_daily_briefing,
    compose_daily_briefing_messages,
    enrich_daily_briefing_avatars,
)
from src.briefings.message import BriefingMessage
from src.briefings.weekly import (
    WeeklyShipBriefing,
    build_weekly_briefing,
    compose_weekly_briefing_messages,
)
from src.config.briefings import (
    BRIEFING_PREVIEW_CHANNEL_ID,
    DAILY_BRIEFING_CONCERNS,
    WEEKLY_BRIEFING_CONCERNS,
)
from src.config.main_server import ENVIRONMENT, GUILD_ID
from src.config.ships import SHIPS
from src.data.repository.ship_briefing_repository import ShipBriefingRepository

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BriefingRunSummary:
    sent_count: int
    failed_count: int


class BriefingPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"


class ShipBriefingRunner:
    def __init__(
        self,
        repository: ShipBriefingRepository,
        *,
        production: bool | None = None,
        user_mentions_enabled: bool | None = None,
        preview_channel_id: int = BRIEFING_PREVIEW_CHANNEL_ID,
        daily_concerns: Mapping[str, bool] = DAILY_BRIEFING_CONCERNS,
        weekly_concerns: Mapping[str, bool] = WEEKLY_BRIEFING_CONCERNS,
    ) -> None:
        self.repository = repository
        self.production = ENVIRONMENT == "PROD" if production is None else production
        self.user_mentions_enabled = (
            self.production if user_mentions_enabled is None else user_mentions_enabled
        )
        self.preview_channel_id = preview_channel_id
        self.daily_concerns = dict(daily_concerns)
        self.weekly_concerns = dict(weekly_concerns)

    async def send_daily_briefings(
        self,
        bot: commands.Bot,
        reference_time: datetime | None = None,
        *,
        ship_role_ids: set[int] | None = None,
        message_target=None,
    ) -> BriefingRunSummary:
        return await self.send_briefings(
            bot,
            BriefingPeriod.DAILY,
            reference_time,
            ship_role_ids=ship_role_ids,
            message_target=message_target,
        )

    async def send_weekly_briefings(
        self,
        bot: commands.Bot,
        reference_time: datetime | None = None,
        *,
        ship_role_ids: set[int] | None = None,
        message_target=None,
    ) -> BriefingRunSummary:
        return await self.send_briefings(
            bot,
            BriefingPeriod.WEEKLY,
            reference_time,
            ship_role_ids=ship_role_ids,
            message_target=message_target,
        )

    async def send_briefings(
        self,
        bot: commands.Bot,
        period: BriefingPeriod,
        reference_time: datetime | None = None,
        *,
        ship_role_ids: set[int] | None = None,
        message_target=None,
    ) -> BriefingRunSummary:
        ships = self._selected_ships(ship_role_ids)
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning(
                "%s ship briefings skipped because the guild is unavailable.",
                period.value.capitalize(),
                extra={
                    "briefing_type": period.value,
                    "delivery_result": "guild_unavailable",
                },
            )
            return BriefingRunSummary(sent_count=0, failed_count=len(ships))

        reference = _ensure_utc(reference_time or datetime.now(UTC))
        sent = 0
        failed = 0
        for ship in ships:
            try:
                role = guild.get_role(ship.role_id)
                if role is None:
                    raise LookupError(f"Ship role {ship.role_id} is unavailable.")
                messages, daily_briefing = await self._compose_messages(
                    period=period,
                    guild=guild,
                    ship=ship,
                    role=role,
                    reference_time=reference,
                )
                if not messages:
                    self._log_delivery(
                        period,
                        ship.role_id,
                        "disabled",
                        daily_briefing,
                    )
                    continue
                channel = message_target or self._get_destination_channel(
                    guild,
                    ship,
                )
                await self._send_messages(channel, messages)
                sent += 1
                self._log_delivery(
                    period,
                    ship.role_id,
                    "sent",
                    daily_briefing,
                )
            except Exception:
                failed += 1
                log.exception(
                    "%s ship briefing failed.",
                    period.value.capitalize(),
                    extra={
                        "briefing_type": period.value,
                        "ship": ship.role_id,
                        "delivery_result": "failed",
                        "notify_engineer": True,
                    },
                )
        return BriefingRunSummary(sent_count=sent, failed_count=failed)

    async def _compose_messages(
        self,
        *,
        period: BriefingPeriod,
        guild,
        ship,
        role,
        reference_time: datetime,
    ) -> tuple[Sequence[BriefingMessage], DailyShipBriefing | None]:
        if period is BriefingPeriod.DAILY:
            briefing = self.build_daily_briefing(
                guild=guild,
                ship_role=role,
                ship_name=ship.name,
                reference_time=reference_time,
            )
            if self.daily_concerns.get("requirements", False):
                briefing = await enrich_daily_briefing_avatars(
                    briefing,
                    members=role.members,
                )
            messages = compose_daily_briefing_messages(
                briefing,
                concerns=self.daily_concerns,
                mentions_enabled=self.user_mentions_enabled,
            )
            return messages, briefing

        briefing = self.build_weekly_briefing(
            ship_role_id=ship.role_id,
            ship_name=ship.name,
            current_ship_size=len(role.members),
            reference_time=reference_time,
        )
        return (
            compose_weekly_briefing_messages(
                briefing,
                concerns=self.weekly_concerns,
            ),
            None,
        )

    def build_daily_briefing(
        self,
        *,
        guild: discord.Guild,
        ship_role,
        ship_name: str,
        reference_time: datetime,
    ) -> DailyShipBriefing:
        return build_daily_briefing(
            self.repository,
            guild=guild,
            ship_role=ship_role,
            ship_name=ship_name,
            reference_time=reference_time,
        )

    def build_weekly_briefing(
        self,
        *,
        ship_role_id: int,
        ship_name: str,
        current_ship_size: int,
        reference_time: datetime,
    ) -> WeeklyShipBriefing:
        return build_weekly_briefing(
            self.repository,
            ship_role_id=ship_role_id,
            ship_name=ship_name,
            current_ship_size=current_ship_size,
            reference_time=reference_time,
        )

    async def _send_messages(
        self,
        channel,
        messages: Sequence[BriefingMessage],
    ) -> None:
        for message in messages:
            allowed_mentions = (
                discord.AllowedMentions(
                    users=True,
                    roles=False,
                    everyone=False,
                )
                if self.user_mentions_enabled and message.allow_user_mentions
                else discord.AllowedMentions.none()
            )
            kwargs = {"allowed_mentions": allowed_mentions}
            if message.embeds:
                kwargs["embeds"] = list(message.embeds)
            if message.files:
                kwargs["files"] = list(message.files)
            await channel.send(message.content, **kwargs)

    def _get_destination_channel(self, guild, ship):
        channel_id = (
            ship.boat_command_channel_id if self.production else self.preview_channel_id
        )
        channel = guild.get_channel(channel_id)
        if channel is None:
            raise LookupError(f"Briefing channel {channel_id} is unavailable.")
        return channel

    @staticmethod
    def _selected_ships(ship_role_ids: set[int] | None):
        if ship_role_ids is None:
            return tuple(SHIPS)
        return tuple(ship for ship in SHIPS if ship.role_id in ship_role_ids)

    def _log_delivery(
        self,
        period: BriefingPeriod,
        ship_role_id: int,
        result: str,
        daily_briefing: DailyShipBriefing | None = None,
    ) -> None:
        requirements_enabled = self.daily_concerns.get("requirements", False)
        awards_enabled = self.daily_concerns.get("awards", False)
        log.info(
            "Ship briefing delivery.",
            extra={
                "briefing_type": period.value,
                "ship": ship_role_id,
                "delivery_result": result,
                "due_soon_count": (
                    daily_briefing.due_soon_count
                    if daily_briefing and requirements_enabled
                    else 0
                ),
                "overdue_count": (
                    daily_briefing.overdue_count
                    if daily_briefing and requirements_enabled
                    else 0
                ),
                "award_count": (
                    len(daily_briefing.pending_awards)
                    if daily_briefing and awards_enabled
                    else 0
                ),
                "action_count": (
                    daily_briefing.action_count_for(self.daily_concerns)
                    if daily_briefing
                    else 0
                ),
            },
        )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
