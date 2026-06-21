from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from logging import getLogger
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from src.analytics.ping_analytics import PingAnalyticsFilters, PingAnalyticsService
from src.analytics.ranges import (
    ANALYTICS_RANGE_OPTIONS as RANGE_OPTIONS,
)
from src.analytics.ranges import (
    ROLE_SIZE_ANALYTICS_RANGE_OPTIONS as ROLE_SIZE_RANGE_OPTIONS,
)
from src.analytics.ranges import (
    SHIP_ANALYTICS_RANGE_OPTIONS as SHIP_RANGE_OPTIONS,
)
from src.analytics.ranges import (
    SHIP_HISTORY_RANGE_OPTIONS,
    TimeRange,
    bucket_label,
    role_size_time_range,
)
from src.analytics.role_size_analytics import (
    RoleSizeAnalyticsFilters,
    RoleSizeAnalyticsService,
)
from src.analytics.ship_analytics import ShipAnalyticsFilters, ShipAnalyticsService
from src.analytics.voyage_analytics import (
    AnalyticsFilters,
    CompanionShare,
    OverviewSummary,
    RankShare,
    VoyageAnalyticsService,
)
from src.cogs.commands.NSC.cooldown_stats import (
    build_cooldown_report_embeds,
    build_cooldown_snapshots,
)
from src.config import IMAGE_CACHES
from src.config.ping_tracking import PING_TRACKING_CONFIG
from src.config.ranks import RANKS
from src.config.ships import (
    ANCIENT_ISLES_FLEET,
    DEVILS_ROAR_FLEET,
    FLEETS_OF_THE_NAVY,
    SHIPS,
    SHORES_OF_PLENTY_FLEET,
    WILDS_FLEET,
)
from src.core.command_cooldowns import normalize_command_name
from src.data.models import RoleType, VoyageType
from src.data.repository.common.base_repository import Session
from src.security import Role, require_any_role
from src.utils.embeds import default_embed, error_embed
from src.utils.image_cache import BinaryImageCache, render_matplotlib_plot_to_png

log = getLogger(__name__)

VOYAGE_ANALYTICS_CACHE = BinaryImageCache(IMAGE_CACHES["voyage_analytics_overview"])

VOYAGE_TYPE_OPTIONS = {
    "all": None,
    "skirmish": VoyageType.SKIRMISH,
    "patrol": VoyageType.PATROL,
    "adventure": VoyageType.ADVENTURE,
    "convoy": VoyageType.CONVOY,
    "unknown": VoyageType.UNKNOWN,
}

SHIP_ROLE_IDS = {ship.role_id for ship in SHIPS}
SHIP_LABEL_BY_ROLE_ID = {ship.role_id: f"{ship.emoji} {ship.name}" for ship in SHIPS}
SHIP_NAME_OPTIONS = {ship.name for ship in FLEETS_OF_THE_NAVY.ships}

FLEET_OPTIONS = {
    "all": (),
    "ancient_isles": tuple(ship.role_id for ship in ANCIENT_ISLES_FLEET.ships),
    "devils_roar": tuple(ship.role_id for ship in DEVILS_ROAR_FLEET.ships),
    "shores_of_plenty": tuple(ship.role_id for ship in SHORES_OF_PLENTY_FLEET.ships),
    "wilds": tuple(ship.role_id for ship in WILDS_FLEET.ships),
}

RANK_GROUP_OPTIONS = {
    "active": "All Active Ranks",
    "all": "All Ranks",
    "e3_up": "Able Seaman & Up",
    "nco_up": "NCOs & Up",
    "snco_up": "Senior NCOs & Up",
    "officer": "Officers",
}

INACTIVE_RANK_NAMES = {"Deckhand", "Recruit", "Retired", "Veteran", "Dungeon Master"}

ANALYTICS_VIEW_TIMEOUT_SECONDS = 300
ALL_VALUE = "all"
TRACKED_PING_ROLE_IDS = tuple(
    dict.fromkeys(
        role_id
        for channel_roles in PING_TRACKING_CONFIG.values()
        for role_id in channel_roles
    )
)


@dataclass
class VoyageFilterState:
    range_label: str = "30d"
    section: Literal["overview", "ranks", "companions"] = "overview"
    ship_role_id: int | None = None
    user_id: int | None = None
    voyage_type: str = ALL_VALUE

    def to_service_filters(self, now: datetime) -> AnalyticsFilters:
        return AnalyticsFilters(
            time_range=TimeRange.from_reference(self.range_label, now),
            ship_role_id=self.ship_role_id,
            user_id=self.user_id,
            voyage_type=VOYAGE_TYPE_OPTIONS.get(self.voyage_type or ALL_VALUE),
        )

    def apply_select(self, field: str, value: str) -> None:
        if field == "range":
            self.range_label = value
        elif field == "ship":
            self.ship_role_id = None if value == ALL_VALUE else int(value)
        elif field == "user":
            self.user_id = None if value == ALL_VALUE else int(value)
        elif field == "voyage_type":
            self.voyage_type = value

    def apply_user(self, field: str, user_id: int) -> None:
        if field == "user":
            self.user_id = user_id

    def clear_optional_filters(self) -> None:
        self.ship_role_id = None
        if self.section != "companions":
            self.user_id = None
        self.voyage_type = ALL_VALUE


@dataclass
class ShipFilterState:
    range_label: str = "30d"
    ship_role_id: int | None = None
    fleet: str = ALL_VALUE
    voyage_type: str = ALL_VALUE
    ship_name: str | None = None
    host_id: int | None = None
    crew_member_id: int | None = None

    def to_activity_filters(self, now: datetime) -> ShipAnalyticsFilters:
        return ShipAnalyticsFilters(
            time_range=TimeRange.from_reference(self.range_label, now),
            ship_role_id=self.ship_role_id,
            fleet_role_ids=FLEET_OPTIONS.get(self.fleet, ()),
            voyage_type=VOYAGE_TYPE_OPTIONS.get(self.voyage_type or ALL_VALUE),
        )

    def to_history_filters(self, now: datetime) -> ShipAnalyticsFilters:
        return ShipAnalyticsFilters(
            time_range=TimeRange.from_reference(self.range_label, now),
            ship_name=self.ship_name,
            host_id=self.host_id,
            crew_member_id=self.crew_member_id,
            voyage_type=VOYAGE_TYPE_OPTIONS.get(self.voyage_type or ALL_VALUE),
        )

    def apply_select(self, field: str, value: str) -> None:
        if field == "range":
            self.range_label = value
        elif field == "ship":
            self.ship_role_id = None if value == ALL_VALUE else int(value)
            if self.ship_role_id is not None:
                self.fleet = ALL_VALUE
        elif field == "fleet":
            self.fleet = value
            if value != ALL_VALUE:
                self.ship_role_id = None
        elif field == "voyage_type":
            self.voyage_type = value
        elif field == "ship_name":
            self.ship_name = value

    def apply_user(self, field: str, user_id: int) -> None:
        if field == "host":
            self.host_id = user_id
        elif field == "crew_member":
            self.crew_member_id = user_id

    def clear_optional_filters(self) -> None:
        self.ship_role_id = None
        self.fleet = ALL_VALUE
        self.voyage_type = ALL_VALUE
        self.host_id = None
        self.crew_member_id = None


@dataclass
class PingFilterState:
    range_label: str = "30d"
    ping_role_id: int | None = None
    ship_role_id: int | None = None
    user_id: int | None = None
    vp_status: str = ALL_VALUE

    def to_service_filters(self, now: datetime) -> PingAnalyticsFilters:
        return PingAnalyticsFilters(
            time_range=TimeRange.from_reference(self.range_label, now),
            ping_role_id=self.ping_role_id,
            ship_role_id=self.ship_role_id,
            user_id=self.user_id,
            has_vp_permission=_vp_status_filter(self.vp_status),
        )

    def apply_select(self, field: str, value: str) -> None:
        if field == "range":
            self.range_label = value
        elif field == "ping_role":
            self.ping_role_id = None if value == ALL_VALUE else int(value)
        elif field == "ship":
            self.ship_role_id = None if value == ALL_VALUE else int(value)
        elif field == "user":
            self.user_id = None if value == ALL_VALUE else int(value)
        elif field == "vp_status":
            self.vp_status = value

    def apply_user(self, field: str, user_id: int) -> None:
        if field == "user":
            self.user_id = user_id

    def clear_optional_filters(self) -> None:
        self.ping_role_id = None
        self.ship_role_id = None
        self.user_id = None
        self.vp_status = ALL_VALUE


@dataclass
class RoleSizeFilterState:
    range_label: str = "90d"
    rank_group: str = "active"
    rank: str | None = None

    def to_service_filters(self, now: datetime) -> RoleSizeAnalyticsFilters:
        return RoleSizeAnalyticsFilters(
            time_range=role_size_time_range(self.range_label, now),
            role_ids=tuple(_rank_role_ids(self.rank_group, self.rank)),
            role_type=RoleType.RANK,
        )

    def apply_select(self, field: str, value: str) -> None:
        if field == "range":
            self.range_label = value
        elif field == "rank_group":
            self.rank_group = value
            self.rank = None
        elif field == "rank":
            self.rank = None if value == ALL_VALUE else value

    def clear_optional_filters(self) -> None:
        self.rank = None


@dataclass
class CooldownFilterState:
    scope: str | None = None

    def clear_optional_filters(self) -> None:
        return None


@dataclass
class _AnalyticsReportPayload:
    embed: discord.Embed | None = None
    embeds: list[discord.Embed] | None = None
    file: discord.File | None = None

    def send_kwargs(
            self,
            view: discord.ui.View,
            *,
            ephemeral: bool,
    ) -> dict:
        kwargs: dict = {
            "view": view,
            "ephemeral": ephemeral,
            "allowed_mentions": discord.AllowedMentions.none(),
        }
        if self.embeds is not None:
            kwargs["embeds"] = self.embeds
        elif self.embed is not None:
            kwargs["embed"] = self.embed
        if self.file is not None:
            kwargs["file"] = self.file
        return kwargs

    def edit_kwargs(self, view: discord.ui.View) -> dict:
        kwargs: dict = {"view": view, "attachments": [self.file] if self.file else []}
        if self.embeds is not None:
            kwargs["embeds"] = self.embeds
        elif self.embed is not None:
            kwargs["embed"] = self.embed
        return kwargs


class _AnalyticsSelect(discord.ui.Select):
    def __init__(
            self,
            *,
            section: str,
            field: str,
            placeholder: str,
            options: list[discord.SelectOption],
            row: int,
    ) -> None:
        super().__init__(
            custom_id=f"analytics:{section}:{field}",
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options[:25],
            row=row,
        )
        self.field = field

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AnalyticsReportView):
            return
        view.state.apply_select(self.field, self.values[0])
        await view.refresh(interaction)


class _AnalyticsUserSelect(discord.ui.UserSelect):
    def __init__(
            self,
            *,
            section: str,
            field: str,
            placeholder: str,
            row: int,
    ) -> None:
        super().__init__(
            custom_id=f"analytics:{section}:{field}",
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            row=row,
        )
        self.field = field

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AnalyticsReportView) or not self.values:
            return
        view.state.apply_user(self.field, self.values[0].id)
        await view.refresh(interaction)


class _RefreshButton(discord.ui.Button):
    def __init__(self, *, section: str, row: int) -> None:
        super().__init__(
            custom_id=f"analytics:{section}:refresh",
            label="Refresh",
            style=discord.ButtonStyle.secondary,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if isinstance(view, AnalyticsReportView):
            await view.refresh(interaction)


class _ClearFiltersButton(discord.ui.Button):
    def __init__(self, *, section: str, row: int) -> None:
        super().__init__(
            custom_id=f"analytics:{section}:clear",
            label="Clear Filters",
            style=discord.ButtonStyle.secondary,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if isinstance(view, AnalyticsReportView):
            view.state.clear_optional_filters()
            await view.refresh(interaction)


class AnalyticsReportView(discord.ui.View):
    def __init__(
            self,
            *,
            cog: AnalyticsHub,
            owner_id: int,
            section: str,
            state: (
                    VoyageFilterState
                    | ShipFilterState
                    | PingFilterState
                    | RoleSizeFilterState
                    | CooldownFilterState
            ),
            hidden: bool,
            guild: discord.Guild | None = None,
    ) -> None:
        super().__init__(timeout=ANALYTICS_VIEW_TIMEOUT_SECONDS)
        self.cog = cog
        self.owner_id = owner_id
        self.section = section
        self.state = state
        self.hidden = hidden
        self.guild = guild
        self.rebuild_items()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.owner_id:
            return True
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Only the user who opened this analytics report can change it.",
                ephemeral=True,
            )
        return False

    def rebuild_items(self) -> None:
        self.clear_items()
        if isinstance(self.state, VoyageFilterState):
            self._add_voyage_items()
        elif isinstance(self.state, ShipFilterState) and self.section == "ships":
            self._add_ship_activity_items()
        elif isinstance(self.state, ShipFilterState):
            self._add_ship_history_items()
        elif isinstance(self.state, PingFilterState):
            self._add_ping_items()
        elif isinstance(self.state, RoleSizeFilterState):
            self._add_role_size_items()
        elif isinstance(self.state, CooldownFilterState):
            self.add_item(_RefreshButton(section=self.section, row=0))

    async def refresh(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        self.guild = interaction.guild or self.guild
        try:
            payload = await self.cog._build_report_payload(self, interaction)
        except Exception as e:
            log.error("Error refreshing analytics report: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=error_embed(
                    title="Analytics unavailable",
                    description="Unable to refresh this analytics report right now.",
                    footer=False,
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        self.rebuild_items()
        await interaction.edit_original_response(**payload.edit_kwargs(self))

    def _add_voyage_items(self) -> None:
        state = self.state
        assert isinstance(state, VoyageFilterState)
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="range",
                placeholder="Select time range...",
                options=_range_options(RANGE_OPTIONS, state.range_label),
                row=0,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="ship",
                placeholder="Filter by ship...",
                options=_ship_options(state.ship_role_id),
                row=1,
            )
        )
        self.add_item(
            _AnalyticsUserSelect(
                section=self.section,
                field="user",
                placeholder=_user_select_placeholder("Filter by user", state.user_id),
                row=2,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="voyage_type",
                placeholder="Filter by voyage type...",
                options=_voyage_type_options(state.voyage_type),
                row=3,
            )
        )
        self.add_item(_RefreshButton(section=self.section, row=4))
        self.add_item(_ClearFiltersButton(section=self.section, row=4))

    def _add_ship_activity_items(self) -> None:
        state = self.state
        assert isinstance(state, ShipFilterState)
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="range",
                placeholder="Select time range...",
                options=_range_options(SHIP_RANGE_OPTIONS, state.range_label),
                row=0,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="ship",
                placeholder="Filter by ship...",
                options=_ship_options(state.ship_role_id),
                row=1,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="fleet",
                placeholder="Filter by fleet...",
                options=_fleet_options(state.fleet),
                row=2,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="voyage_type",
                placeholder="Filter by voyage type...",
                options=_voyage_type_options(state.voyage_type),
                row=3,
            )
        )
        self.add_item(_RefreshButton(section=self.section, row=4))
        self.add_item(_ClearFiltersButton(section=self.section, row=4))

    def _add_ship_history_items(self) -> None:
        state = self.state
        assert isinstance(state, ShipFilterState)
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="ship_name",
                placeholder="Select ship name...",
                options=_ship_name_options(state.ship_name),
                row=0,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="range",
                placeholder="Select time range...",
                options=_range_options(SHIP_HISTORY_RANGE_OPTIONS, state.range_label),
                row=1,
            )
        )
        self.add_item(
            _AnalyticsUserSelect(
                section=self.section,
                field="host",
                placeholder=_user_select_placeholder("Filter by host", state.host_id),
                row=2,
            )
        )
        self.add_item(
            _AnalyticsUserSelect(
                section=self.section,
                field="crew_member",
                placeholder=_user_select_placeholder(
                    "Filter by crew member",
                    state.crew_member_id,
                ),
                row=3,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="voyage_type",
                placeholder="Filter by voyage type...",
                options=_voyage_type_options(state.voyage_type),
                row=4,
            )
        )

    def _add_ping_items(self) -> None:
        state = self.state
        assert isinstance(state, PingFilterState)
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="range",
                placeholder="Select time range...",
                options=_range_options(RANGE_OPTIONS, state.range_label),
                row=0,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="ping_role",
                placeholder="Filter by ping role...",
                options=_ping_role_options(state.ping_role_id, self.guild),
                row=1,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="ship",
                placeholder="Filter by ship...",
                options=_ship_options(state.ship_role_id),
                row=2,
            )
        )
        self.add_item(
            _AnalyticsUserSelect(
                section=self.section,
                field="user",
                placeholder=_user_select_placeholder("Filter by user", state.user_id),
                row=3,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="vp_status",
                placeholder="Filter by VP status...",
                options=_vp_status_options(state.vp_status),
                row=4,
            )
        )

    def _add_role_size_items(self) -> None:
        state = self.state
        assert isinstance(state, RoleSizeFilterState)
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="range",
                placeholder="Select time range...",
                options=_range_options(ROLE_SIZE_RANGE_OPTIONS, state.range_label),
                row=0,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="rank_group",
                placeholder="Filter by rank group...",
                options=_rank_group_options(state.rank_group),
                row=1,
            )
        )
        self.add_item(
            _AnalyticsSelect(
                section=self.section,
                field="rank",
                placeholder="Zoom into a single rank...",
                options=_rank_options(state.rank),
                row=2,
            )
        )
        self.add_item(_RefreshButton(section=self.section, row=3))
        self.add_item(_ClearFiltersButton(section=self.section, row=3))


class AnalyticsHub(commands.GroupCog, name="analytics"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _send_interactive_report(
            self,
            interaction: discord.Interaction,
            view: AnalyticsReportView,
            *,
            unavailable_title: str,
    ) -> None:
        try:
            payload = await self._build_report_payload(view, interaction)
        except KeyError:
            raise
        except Exception as e:
            log.error("Error generating analytics report: %s", e, exc_info=True)
            await _send_unavailable(interaction, unavailable_title)
            return

        await interaction.followup.send(
            **payload.send_kwargs(view, ephemeral=view.hidden),
        )

    async def _build_report_payload(
            self,
            view: AnalyticsReportView,
            interaction: discord.Interaction,
    ) -> _AnalyticsReportPayload:
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        state = view.state
        if isinstance(state, VoyageFilterState):
            return await self._build_voyage_payload(state, interaction, now)
        if isinstance(state, ShipFilterState) and view.section == "ships":
            return await self._build_ship_activity_payload(state, now)
        if isinstance(state, ShipFilterState):
            return await self._build_ship_history_payload(state, now)
        if isinstance(state, PingFilterState):
            return await self._build_ping_payload(state, now)
        if isinstance(state, RoleSizeFilterState):
            return await self._build_role_size_payload(state, now)
        if isinstance(state, CooldownFilterState):
            embeds = await asyncio.to_thread(build_cooldown_report_embeds, state.scope)
            return _AnalyticsReportPayload(embeds=embeds)
        msg = f"Unsupported analytics state: {type(state)!r}"
        raise TypeError(msg)

    async def _build_voyage_payload(
            self,
            state: VoyageFilterState,
            interaction: discord.Interaction,
            now: datetime,
    ) -> _AnalyticsReportPayload:
        if state.section == "companions" and state.user_id is None:
            msg = "Companion analytics require a user filter."
            raise ValueError(msg)

        filters = state.to_service_filters(now)
        ship = _guild_role(interaction.guild, filters.ship_role_id)
        user = _guild_member(interaction.guild, filters.user_id)
        session = Session()
        try:
            service = VoyageAnalyticsService(session)
            if state.section == "ranks":
                rank_share = await asyncio.to_thread(service.build_rank_share, filters)
                embed, file = await asyncio.to_thread(
                    _render_rank_share,
                    rank_share,
                    ship,
                    user,
                )
            elif state.section == "companions":
                companion_share = await asyncio.to_thread(
                    service.build_companion_share,
                    filters,
                )
                embed, file = await asyncio.to_thread(
                    _render_companion_share,
                    companion_share,
                    ship,
                    user,
                )
            else:
                overview = await asyncio.to_thread(service.build_overview, filters)
                embed, file = await asyncio.to_thread(
                    _render_overview,
                    overview,
                    ship,
                    user,
                )
            return _AnalyticsReportPayload(embed=embed, file=file)
        finally:
            session.close()

    async def _build_ship_activity_payload(
            self,
            state: ShipFilterState,
            now: datetime,
    ) -> _AnalyticsReportPayload:
        filters = state.to_activity_filters(now)
        session = Session()
        try:
            summary = await asyncio.to_thread(
                ShipAnalyticsService(session).build_activity,
                filters,
            )
            embed, file = await asyncio.to_thread(_render_ship_activity, summary)
            return _AnalyticsReportPayload(embed=embed, file=file)
        finally:
            session.close()

    async def _build_ship_history_payload(
            self,
            state: ShipFilterState,
            now: datetime,
    ) -> _AnalyticsReportPayload:
        filters = state.to_history_filters(now)
        session = Session()
        try:
            summary = await asyncio.to_thread(
                ShipAnalyticsService(session).build_history,
                filters,
            )
            embed = _render_ship_history(summary)
            return _AnalyticsReportPayload(embed=embed)
        finally:
            session.close()

    async def _build_ping_payload(
            self,
            state: PingFilterState,
            now: datetime,
    ) -> _AnalyticsReportPayload:
        filters = state.to_service_filters(now)
        session = Session()
        try:
            summary = await asyncio.to_thread(
                PingAnalyticsService(session).build_summary,
                filters,
            )
            embed, file = await asyncio.to_thread(_render_ping_summary, summary)
            return _AnalyticsReportPayload(embed=embed, file=file)
        finally:
            session.close()

    async def _build_role_size_payload(
            self,
            state: RoleSizeFilterState,
            now: datetime,
    ) -> _AnalyticsReportPayload:
        filters = state.to_service_filters(now)
        session = Session()
        try:
            summary = await asyncio.to_thread(
                RoleSizeAnalyticsService(session).build_summary,
                filters,
            )
            embed, file = await asyncio.to_thread(
                _render_role_size_summary,
                summary,
                state.rank_group,
                state.rank,
            )
            return _AnalyticsReportPayload(embed=embed, file=file)
        finally:
            session.close()

    @app_commands.command(
        name="voyages",
        description="Voyage activity, loot, ships, hosts, and subclass analytics.",
    )
    @app_commands.describe(
        range="Time range to analyze.",
        ship="Optional ship filter. Must be a configured ship role.",
        user="Optional attributable user filter.",
        voyage_type="Optional voyage type filter parsed from hosted voyage logs.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[app_commands.Choice(name=value, value=value) for value in RANGE_OPTIONS],
        voyage_type=[
            app_commands.Choice(name="All voyage types", value="all"),
            app_commands.Choice(name="Skirmish", value="skirmish"),
            app_commands.Choice(name="Patrol", value="patrol"),
            app_commands.Choice(name="Adventure", value="adventure"),
            app_commands.Choice(name="Convoy", value="convoy"),
            app_commands.Choice(name="Unknown", value="unknown"),
        ],
    )
    @require_any_role(
        Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR
    )
    async def voyages(
            self,
            interaction: discord.Interaction,
            range: str = "30d",
            ship: discord.Role | None = None,
            user: discord.Member | None = None,
            voyage_type: str = "all",
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        if not await _validate_ship_filter(interaction, ship):
            return
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="voyages",
            state=VoyageFilterState(
                range_label=range,
                section="overview",
                ship_role_id=ship.id if ship else None,
                user_id=user.id if user else None,
                voyage_type=voyage_type,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Voyage analytics unavailable",
        )

    @app_commands.command(
        name="voyage-ranks",
        description="Voyage participant rank share using stored voyage-time ranks.",
    )
    @app_commands.describe(
        range="Time range to analyze.",
        ship="Optional ship filter. Must be a configured ship role.",
        user="Optional attributable user filter.",
        voyage_type="Optional voyage type filter parsed from hosted voyage logs.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[app_commands.Choice(name=value, value=value) for value in RANGE_OPTIONS],
        voyage_type=[
            app_commands.Choice(name="All voyage types", value="all"),
            app_commands.Choice(name="Skirmish", value="skirmish"),
            app_commands.Choice(name="Patrol", value="patrol"),
            app_commands.Choice(name="Adventure", value="adventure"),
            app_commands.Choice(name="Convoy", value="convoy"),
            app_commands.Choice(name="Unknown", value="unknown"),
        ],
    )
    @require_any_role(
        Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR
    )
    async def voyage_ranks(
            self,
            interaction: discord.Interaction,
            range: str = "30d",
            ship: discord.Role | None = None,
            user: discord.Member | None = None,
            voyage_type: str = "all",
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        if not await _validate_ship_filter(interaction, ship):
            return
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="voyage-ranks",
            state=VoyageFilterState(
                range_label=range,
                section="ranks",
                ship_role_id=ship.id if ship else None,
                user_id=user.id if user else None,
                voyage_type=voyage_type,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Voyage analytics unavailable",
        )

    @app_commands.command(
        name="companions",
        description="User voyage companions, companion rank share, and ship share.",
    )
    @app_commands.describe(
        user="User to analyze.",
        range="Time range to analyze.",
        ship="Optional ship filter. Must be a configured ship role.",
        voyage_type="Optional voyage type filter parsed from hosted voyage logs.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[app_commands.Choice(name=value, value=value) for value in RANGE_OPTIONS],
        voyage_type=[
            app_commands.Choice(name="All voyage types", value="all"),
            app_commands.Choice(name="Skirmish", value="skirmish"),
            app_commands.Choice(name="Patrol", value="patrol"),
            app_commands.Choice(name="Adventure", value="adventure"),
            app_commands.Choice(name="Convoy", value="convoy"),
            app_commands.Choice(name="Unknown", value="unknown"),
        ],
    )
    @require_any_role(
        Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR
    )
    async def companions(
            self,
            interaction: discord.Interaction,
            user: discord.Member,
            range: str = "30d",
            ship: discord.Role | None = None,
            voyage_type: str = "all",
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        if not await _validate_ship_filter(interaction, ship):
            return
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="companions",
            state=VoyageFilterState(
                range_label=range,
                section="companions",
                ship_role_id=ship.id if ship else None,
                user_id=user.id,
                voyage_type=voyage_type,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Voyage analytics unavailable",
        )

    @app_commands.command(
        name="ships",
        description="Ship activity, performers, voyage types, and trend analytics.",
    )
    @app_commands.describe(
        range="Time range to analyze.",
        ship="Optional ship filter. Must be a configured ship role.",
        fleet="Optional fleet filter.",
        voyage_type="Optional voyage type filter parsed from hosted voyage logs.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[
            app_commands.Choice(name=value, value=value)
            for value in SHIP_RANGE_OPTIONS
        ],
        fleet=[
            app_commands.Choice(name="All fleets", value="all"),
            app_commands.Choice(name="Ancient Isles", value="ancient_isles"),
            app_commands.Choice(name="Devil's Roar", value="devils_roar"),
            app_commands.Choice(name="Shores of Plenty", value="shores_of_plenty"),
            app_commands.Choice(name="Wilds", value="wilds"),
        ],
        voyage_type=[
            app_commands.Choice(name="All voyage types", value="all"),
            app_commands.Choice(name="Skirmish", value="skirmish"),
            app_commands.Choice(name="Patrol", value="patrol"),
            app_commands.Choice(name="Adventure", value="adventure"),
            app_commands.Choice(name="Convoy", value="convoy"),
            app_commands.Choice(name="Unknown", value="unknown"),
        ],
    )
    @require_any_role(
        Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR
    )
    async def ships(
            self,
            interaction: discord.Interaction,
            range: str = "30d",
            ship: discord.Role | None = None,
            fleet: str = "all",
            voyage_type: str = "all",
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        if not await _validate_ship_filter(interaction, ship):
            return
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="ships",
            state=ShipFilterState(
                range_label=range,
                ship_role_id=ship.id if ship else None,
                fleet=fleet,
                voyage_type=voyage_type,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Ship analytics unavailable",
        )

    @app_commands.command(
        name="ship-history",
        description="History for a named ship, including hosts, loot, and recent logs.",
    )
    @app_commands.describe(
        ship_name="Exact persisted ship name, for example USS Venom.",
        range="Time range to analyze.",
        voyage_type="Optional voyage type filter parsed from hosted voyage logs.",
        host="Optional host filter.",
        crew_member="Optional crew member filter.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[
            app_commands.Choice(name=value, value=value)
            for value in SHIP_HISTORY_RANGE_OPTIONS
        ],
        voyage_type=[
            app_commands.Choice(name="All voyage types", value="all"),
            app_commands.Choice(name="Skirmish", value="skirmish"),
            app_commands.Choice(name="Patrol", value="patrol"),
            app_commands.Choice(name="Adventure", value="adventure"),
            app_commands.Choice(name="Convoy", value="convoy"),
            app_commands.Choice(name="Unknown", value="unknown"),
        ],
    )
    @require_any_role(
        Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR
    )
    async def ship_history(
            self,
            interaction: discord.Interaction,
            ship_name: str,
            range: str = "365d",
            voyage_type: str = "all",
            host: discord.Member | None = None,
            crew_member: discord.Member | None = None,
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="ship-history",
            state=ShipFilterState(
                range_label=range,
                voyage_type=voyage_type,
                ship_name=ship_name,
                host_id=host.id if host else None,
                crew_member_id=crew_member.id if crew_member else None,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Ship history analytics unavailable",
        )

    @app_commands.command(
        name="pings",
        description="LFG ping usage, VP status, rank, ship, and user attribution.",
    )
    @app_commands.describe(
        range="Time range to analyze.",
        ping_role="Optional ping role filter.",
        ship="Optional ship filter from ping-time attribution.",
        user="Optional ping author filter.",
        vp_status="Optional Voyage Permissions status filter.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[app_commands.Choice(name=value, value=value) for value in RANGE_OPTIONS],
        vp_status=[
            app_commands.Choice(name="All", value="all"),
            app_commands.Choice(name="VP enabled", value="vp"),
            app_commands.Choice(name="Non-VP", value="non_vp"),
        ],
    )
    @require_any_role(
        Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR
    )
    async def pings(
            self,
            interaction: discord.Interaction,
            range: str = "30d",
            ping_role: discord.Role | None = None,
            ship: discord.Role | None = None,
            user: discord.Member | None = None,
            vp_status: str = "all",
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        if not await _validate_ship_filter(interaction, ship):
            return
        if not await _validate_ping_role_filter(interaction, ping_role):
            return
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="pings",
            state=PingFilterState(
                range_label=range,
                ping_role_id=ping_role.id if ping_role else None,
                ship_role_id=ship.id if ship else None,
                user_id=user.id if user else None,
                vp_status=vp_status,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Ping analytics unavailable",
        )

    @app_commands.command(
        name="rank-size",
        description=(
                "Rank or ship size trend snapshots. User filters are not meaningful here."
        ),
    )
    @app_commands.describe(
        range="Time range to analyze. Role-size analytics use day/week/month buckets.",
        rank_group="Rank group to include.",
        rank="Optional exact rank identifier, such as E4 or O1.",
        hidden="Should only you be able to see the response?",
    )
    @app_commands.choices(
        range=[
            app_commands.Choice(name=value, value=value)
            for value in ROLE_SIZE_RANGE_OPTIONS
        ],
        rank_group=[
            app_commands.Choice(name=label, value=value)
            for value, label in RANK_GROUP_OPTIONS.items()
        ],
    )
    @require_any_role(Role.BOA, Role.NSC_ADMINISTRATOR)
    async def rank_size(
            self,
            interaction: discord.Interaction,
            range: str = "90d",
            rank_group: str = "active",
            rank: str | None = None,
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="rank-size",
            state=RoleSizeFilterState(
                range_label=range,
                rank_group=rank_group,
                rank=rank,
            ),
            hidden=hidden,
            guild=interaction.guild,
        )
        await self._send_interactive_report(
            interaction,
            view,
            unavailable_title="Rank-size analytics unavailable",
        )

    @app_commands.command(
        name="cooldowns",
        description="Configured cooldowns and tracked cooldown hits.",
    )
    @app_commands.describe(
        scope="Optional command name to inspect.",
        hidden="Should only you be able to see the response?",
    )
    @require_any_role(Role.NSC_OBSERVER)
    async def cooldowns(
            self,
            interaction: discord.Interaction,
            scope: str | None = None,
            hidden: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=hidden)
        view = AnalyticsReportView(
            cog=self,
            owner_id=interaction.user.id,
            section="cooldowns",
            state=CooldownFilterState(scope=scope),
            hidden=hidden,
            guild=interaction.guild,
        )
        try:
            await self._send_interactive_report(
                interaction,
                view,
                unavailable_title="Cooldown analytics unavailable",
            )
        except KeyError:
            await interaction.followup.send(
                embed=error_embed(
                    title="Unknown command",
                    description=f"Unknown command: `{scope}`",
                    footer=False,
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

    @cooldowns.autocomplete("scope")
    async def cooldowns_scope_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> list[app_commands.Choice[str]]:
        del interaction
        current_lower = normalize_command_name(current)
        matching_options = [
            option
            for option in sorted(build_cooldown_snapshots())
            if current_lower in option.lower()
        ]
        return [
            app_commands.Choice(name=option, value=option)
            for option in matching_options[:25]
        ]


def _select_option(
        *,
        label: str,
        value: str,
        current: str | int | None,
        description: str | None = None,
) -> discord.SelectOption:
    current_value = ALL_VALUE if current is None else str(current)
    return discord.SelectOption(
        label=label[:100],
        value=value,
        description=description[:100] if description else None,
        default=value == current_value,
    )


def _range_options(
        values: tuple[str, ...],
        current: str,
) -> list[discord.SelectOption]:
    return [
        _select_option(label=value, value=value, current=current)
        for value in values
    ]


def _ship_options(current_role_id: int | None) -> list[discord.SelectOption]:
    options = [
        _select_option(
            label="All ships",
            value=ALL_VALUE,
            current=current_role_id,
            description="Do not filter by ship.",
        )
    ]
    options.extend(
        _select_option(
            label=ship.name,
            value=str(ship.role_id),
            current=current_role_id,
            description="Use persisted voyage-time ship attribution.",
        )
        for ship in SHIPS
    )
    return options


def _fleet_options(current: str) -> list[discord.SelectOption]:
    labels = {
        "all": "All fleets",
        "ancient_isles": "Ancient Isles",
        "devils_roar": "Devil's Roar",
        "shores_of_plenty": "Shores of Plenty",
        "wilds": "Wilds",
    }
    return [
        _select_option(label=label, value=value, current=current)
        for value, label in labels.items()
    ]


def _voyage_type_options(current: str) -> list[discord.SelectOption]:
    labels = {
        "all": "All voyage types",
        "skirmish": "Skirmish",
        "patrol": "Patrol",
        "adventure": "Adventure",
        "convoy": "Convoy",
        "unknown": "Unknown",
    }
    return [
        _select_option(label=label, value=value, current=current)
        for value, label in labels.items()
    ]


def _ship_name_options(current: str | None) -> list[discord.SelectOption]:
    ship_names = sorted(SHIP_NAME_OPTIONS)
    if current and current not in ship_names:
        ship_names.insert(0, current)
    return [
        _select_option(label=name, value=name, current=current or "")
        for name in ship_names
    ][:25]


def _ping_role_options(
        current_role_id: int | None,
        guild: discord.Guild | None,
) -> list[discord.SelectOption]:
    options = [
        _select_option(
            label="All tracked ping roles",
            value=ALL_VALUE,
            current=current_role_id,
            description="Aggregate all configured LFG ping roles.",
        )
    ]
    for role_id in TRACKED_PING_ROLE_IDS:
        role = guild.get_role(role_id) if guild else None
        options.append(
            _select_option(
                label=role.name if role else f"Role {role_id}",
                value=str(role_id),
                current=current_role_id,
                description="Configured tracked ping role.",
            )
        )
    return options


def _vp_status_options(current: str) -> list[discord.SelectOption]:
    return [
        _select_option(label="All VP statuses", value=ALL_VALUE, current=current),
        _select_option(label="VP enabled", value="vp", current=current),
        _select_option(label="Non-VP", value="non_vp", current=current),
    ]


def _rank_group_options(current: str) -> list[discord.SelectOption]:
    return [
        _select_option(label=label, value=value, current=current)
        for value, label in RANK_GROUP_OPTIONS.items()
    ]


def _rank_options(current: str | None) -> list[discord.SelectOption]:
    options = [
        _select_option(
            label="All ranks in selected group",
            value=ALL_VALUE,
            current=current,
        )
    ]
    for rank in RANKS:
        if rank.name == "Dungeon Master":
            continue
        options.append(
            _select_option(
                label=rank.name,
                value=rank.identifier,
                current=current,
                description=rank.identifier,
            )
        )
    return options[:25]


def _user_select_placeholder(prefix: str, user_id: int | None) -> str:
    if user_id is None:
        return f"{prefix}..."
    return f"{prefix}: {user_id}"


def _guild_role(
        guild: discord.Guild | None,
        role_id: int | None,
) -> discord.Role | None:
    if guild is None or role_id is None:
        return None
    return guild.get_role(role_id)


def _guild_member(
        guild: discord.Guild | None,
        user_id: int | None,
) -> discord.Member | None:
    if guild is None or user_id is None:
        return None
    return guild.get_member(user_id)


def _render_overview(
        summary: OverviewSummary,
        ship: discord.Role | None,
        user: discord.Member | None,
) -> tuple[discord.Embed, discord.File]:
    chart_data = VOYAGE_ANALYTICS_CACHE.get_or_create_bytes(
        _overview_cache_payload(summary),
        lambda: render_matplotlib_plot_to_png(lambda: _plot_overview(summary)),
    )
    file = VOYAGE_ANALYTICS_CACHE.to_discord_file(chart_data)

    embed = default_embed(
        title="Voyage Analytics",
        description=_filter_description(summary.filters, ship, user),
    )
    embed.set_image(url=f"attachment://{file.filename}")
    embed.add_field(
        name="Activity",
        value=(
            f"Voyage attendances: **{summary.total_voyages}**\n"
            f"Unique voyage logs: **{summary.unique_voyage_logs}**\n"
            f"Unique sailors: **{summary.unique_sailors}**\n"
            f"Hosted voyages: **{summary.total_hosted}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="Recovered Loot",
        value=(
            f"Gold: **{summary.total_gold:,}**\n"
            f"Doubloons: **{summary.total_doubloons:,}**\n"
            f"Ancient Coins: **{summary.total_ancient_coins:,}**\n"
            f"Fish: **{summary.total_fish:,}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="Voyage Types",
        value=_format_enum_counts(summary.voyage_type_counts) or "No typed voyages.",
        inline=True,
    )
    embed.add_field(
        name="Top Voyagers",
        value=_format_user_counts(summary.top_voyagers) or "No voyage rows.",
        inline=True,
    )
    embed.add_field(
        name="Top Hosts",
        value=_format_user_counts(summary.top_hosts) or "No hosted rows.",
        inline=True,
    )
    embed.add_field(
        name="Top Ships",
        value=_format_ship_counts(summary.top_ships_by_voyages) or "No ship rows.",
        inline=True,
    )
    embed.add_field(
        name="Subclass Points",
        value=_format_enum_counts(summary.subclass_points) or "No subclass points.",
        inline=False,
    )
    embed.set_footer(text=_data_integrity_footer(summary.filters))
    return embed, file


def _render_rank_share(
        rank_share: RankShare,
        ship: discord.Role | None,
        user: discord.Member | None,
) -> tuple[discord.Embed, discord.File]:
    chart_data = VOYAGE_ANALYTICS_CACHE.get_or_create_bytes(
        {
            "section": "ranks",
            "filters": _filter_cache_payload(rank_share.filters),
            "rank_counts": rank_share.rank_counts,
            "fallback_count": rank_share.fallback_count,
            "unknown_count": rank_share.unknown_count,
        },
        lambda: render_matplotlib_plot_to_png(lambda: _plot_rank_share(rank_share)),
    )
    file = VOYAGE_ANALYTICS_CACHE.to_discord_file(chart_data)
    total = sum(rank_share.rank_counts.values()) + rank_share.unknown_count

    embed = default_embed(
        title="Voyage Analytics: Rank Share",
        description=_filter_description(rank_share.filters, ship, user),
    )
    embed.set_image(url=f"attachment://{file.filename}")
    embed.add_field(
        name="Rank Distribution",
        value=_format_named_counts(rank_share.rank_counts) or "No rank data.",
        inline=False,
    )
    embed.add_field(
        name="Integrity",
        value=(
            f"Attributed voyage rows: **{total}**\n"
            f"Used stored voyage rank where present.\n"
            f"Current-rank fallbacks: **{rank_share.fallback_count}**\n"
            f"Unknown rank rows: **{rank_share.unknown_count}**"
        ),
        inline=False,
    )
    embed.set_footer(text=_data_integrity_footer(rank_share.filters))
    return embed, file


def _render_companion_share(
        companion_share: CompanionShare,
        ship: discord.Role | None,
        user: discord.Member | None,
) -> tuple[discord.Embed, discord.File]:
    chart_data = VOYAGE_ANALYTICS_CACHE.get_or_create_bytes(
        {
            "section": "companions",
            "filters": _filter_cache_payload(companion_share.filters),
            "companions": companion_share.companion_counts,
            "ranks": companion_share.companion_rank_counts,
            "ships": companion_share.companion_ship_counts,
            "shared_voyage_count": companion_share.shared_voyage_count,
        },
        lambda: render_matplotlib_plot_to_png(
            lambda: _plot_companions(companion_share)
        ),
    )
    file = VOYAGE_ANALYTICS_CACHE.to_discord_file(chart_data)

    embed = default_embed(
        title="Voyage Analytics: User Companions",
        description=_filter_description(companion_share.filters, ship, user),
    )
    embed.set_image(url=f"attachment://{file.filename}")
    embed.add_field(
        name="Top Sailors Voyaged With",
        value=_format_user_counts_with_percent(
            companion_share.companion_counts,
            companion_share.shared_voyage_count,
        )
              or "No companion rows.",
        inline=False,
    )
    embed.add_field(
        name="Companion Rank Share",
        value=_format_named_counts_with_percent(
            companion_share.companion_rank_counts,
            sum(companion_share.companion_rank_counts.values()),
        )
              or "No rank data.",
        inline=True,
    )
    embed.add_field(
        name="Companion Ship Share",
        value=_format_ship_counts_with_percent(
            companion_share.companion_ship_counts.items(),
            sum(companion_share.companion_ship_counts.values()),
        )
              or "No ship data.",
        inline=True,
    )
    embed.add_field(
        name="Integrity",
        value=(
            f"Distinct shared voyage logs: **{companion_share.shared_voyage_count}**\n"
            "Companion ranks use stored participant rank first.\n"
            f"Current-rank fallbacks: **{companion_share.fallback_rank_count}**"
        ),
        inline=False,
    )
    embed.set_footer(text=_data_integrity_footer(companion_share.filters))
    return embed, file


def _render_ship_activity(summary) -> tuple[discord.Embed, discord.File]:
    chart_data = VOYAGE_ANALYTICS_CACHE.get_or_create_bytes(
        {
            "section": "ships",
            "filters": _ship_filter_cache_payload(summary.filters),
            "series": [
                {
                    "start": bucket.start.isoformat(),
                    "hosted": bucket.hosted,
                    "voyages": bucket.voyages,
                }
                for bucket in summary.bucket_series
            ],
            "rows": [
                {
                    "ship_role_id": row.ship_role_id,
                    "hosted": row.hosted,
                    "voyages": row.voyages,
                }
                for row in summary.ship_rows
            ],
            "companion_pairs": [
                {
                    "user_one_id": pair.user_one_id,
                    "user_two_id": pair.user_two_id,
                    "shared_voyages": pair.shared_voyages,
                }
                for pair in summary.top_companion_pairs
            ],
            "ship_pairs": [
                {
                    "ship_one_role_id": pair.ship_one_role_id,
                    "ship_two_role_id": pair.ship_two_role_id,
                    "shared_voyages": pair.shared_voyages,
                }
                for pair in summary.top_ship_pairs
            ],
            "ship_pairings": [
                {
                    "ship_role_ids": list(pairing.ship_role_ids),
                    "participant_count": pairing.participant_count,
                }
                for pairing in summary.top_ship_pairings
            ],
            "ship_pairing_participants": summary.ship_pairing_participants,
        },
        lambda: render_matplotlib_plot_to_png(lambda: _plot_ship_activity(summary)),
    )
    file = VOYAGE_ANALYTICS_CACHE.to_discord_file(chart_data)
    embed = default_embed(
        title="Analytics: Ships",
        description=_ship_filter_description(summary.filters),
    )
    embed.set_image(url=f"attachment://{file.filename}")
    embed.add_field(
        name="Activity",
        value=(
            f"Hosted voyages: **{summary.total_hosted}**\n"
            f"Voyage attendances: **{summary.total_voyages}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="Top Hosts",
        value=_format_user_counts(summary.top_hosts) or "No hosted rows.",
        inline=True,
    )
    embed.add_field(
        name="Top Voyagers",
        value=_format_user_counts(summary.top_voyagers) or "No voyage rows.",
        inline=True,
    )
    embed.add_field(
        name="Ships",
        value=_format_ship_activity_rows(summary.ship_rows) or "No ship rows.",
        inline=False,
    )
    embed.add_field(
        name="Common Crew Pairings",
        value=_format_pair_counts_with_percent(
            [
                ((pair.user_one_id, pair.user_two_id), pair.shared_voyages)
                for pair in summary.top_companion_pairs
            ],
            summary.unique_voyage_logs,
        )
              or "No shared crew pairings.",
        inline=False,
    )
    embed.add_field(
        name="Common Ship Pairings",
        value=_format_ship_pairing_counts_with_percent(
            [
                (
                    pairing.ship_role_ids,
                    pairing.participant_count,
                )
                for pairing in summary.top_ship_pairings
            ],
            summary.ship_pairing_participants,
        )
              or "No shared ship pairings.",
        inline=False,
    )
    embed.add_field(
        name="Voyage Types",
        value=_format_enum_counts(summary.voyage_type_counts) or "No typed voyages.",
        inline=False,
    )
    embed.set_footer(
        text=(
            "Source: persisted Hosted and Voyages rows; ship attribution is "
            "voyage-time ship_role_id."
        )
    )
    return embed, file


def _render_ship_history(summary) -> discord.Embed:
    embed = default_embed(
        title="Analytics: Ship History",
        description=_ship_filter_description(summary.filters),
    )
    embed.add_field(
        name="Logs",
        value=f"Hosted logs: **{summary.total_logs}**",
        inline=True,
    )
    embed.add_field(
        name="Recovered Loot",
        value=(
            f"Gold: **{summary.total_gold:,}**\n"
            f"Doubloons: **{summary.total_doubloons:,}**\n"
            f"Ancient Coins: **{summary.total_ancient_coins:,}**\n"
            f"Fish: **{summary.total_fish:,}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="Top Hosts",
        value=_format_user_counts(summary.top_hosts) or "No hosted rows.",
        inline=True,
    )
    embed.add_field(
        name="Voyage Types",
        value=_format_enum_counts(summary.voyage_type_counts) or "No typed voyages.",
        inline=False,
    )
    embed.add_field(
        name="Recent Logs",
        value="\n".join(f"`{log_id}`" for log_id in summary.recent_logs)
              or "No logs found.",
        inline=False,
    )
    embed.set_footer(
        text="Source: persisted Hosted rows; ship names are parsed from voyage logs."
    )
    return embed


def _render_ping_summary(summary) -> tuple[discord.Embed, discord.File]:
    chart_data = VOYAGE_ANALYTICS_CACHE.get_or_create_bytes(
        {
            "section": "pings",
            "filters": _ping_filter_cache_payload(summary.filters),
            "series": [
                {
                    "start": bucket.start.isoformat(),
                    "total": bucket.total,
                    "vp": bucket.vp_enabled,
                    "non_vp": bucket.non_vp,
                }
                for bucket in summary.bucket_series
            ],
        },
        lambda: render_matplotlib_plot_to_png(lambda: _plot_ping_summary(summary)),
    )
    file = VOYAGE_ANALYTICS_CACHE.to_discord_file(chart_data)
    embed = default_embed(
        title="Analytics: Pings",
        description=_ping_filter_description(summary.filters),
    )
    embed.set_image(url=f"attachment://{file.filename}")
    embed.add_field(name="Total Pings", value=f"**{summary.total_pings}**", inline=True)
    embed.add_field(
        name="VP Status",
        value=(
            f"VP enabled: **{summary.vp_enabled_pings}**\n"
            f"Non-VP: **{summary.non_vp_pings}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="Deleted Rows Excluded",
        value=f"**{summary.deleted_rows_excluded}**",
        inline=True,
    )
    embed.add_field(
        name="Top Users",
        value=_format_user_counts(summary.user_counts) or "No ping rows.",
        inline=True,
    )
    embed.add_field(
        name="Ships",
        value=_format_ship_counts(summary.ship_counts.items()) or "No ship data.",
        inline=True,
    )
    embed.add_field(
        name="Ranks",
        value=_format_role_id_counts(summary.rank_counts) or "No rank data.",
        inline=True,
    )
    embed.set_footer(
        text="Source: RolePingLog rows; rank and ship are ping-time snapshots."
    )
    return embed, file


def _render_role_size_summary(summary, rank_group: str, rank: str | None):
    chart_data = VOYAGE_ANALYTICS_CACHE.get_or_create_bytes(
        {
            "section": "rank-size",
            "range": summary.filters.time_range.label,
            "bucket": summary.filters.time_range.bucket,
            "rank_group": rank_group,
            "rank": rank,
            "series": {
                role_id: [
                    {
                        "start": point.start.isoformat(),
                        "member_count": point.member_count,
                    }
                    for point in points
                ]
                for role_id, points in summary.series.items()
            },
        },
        lambda: render_matplotlib_plot_to_png(
            lambda: _plot_role_size_summary(summary)
        ),
    )
    file = VOYAGE_ANALYTICS_CACHE.to_discord_file(chart_data)
    current_counts = {
        role_id: points[-1].member_count
        for role_id, points in summary.series.items()
        if points
    }
    embed = default_embed(
        title="Analytics: Rank Size",
        description=(
                f"Range: **{summary.filters.time_range.label}**, "
                f"bucketed by **{summary.filters.time_range.bucket}**.\n"
                f"Rank group: **{RANK_GROUP_OPTIONS.get(rank_group, rank_group)}**"
                + (f" | Rank: **{rank}**" if rank else "")
        ),
    )
    embed.set_image(url=f"attachment://{file.filename}")
    embed.add_field(
        name="Current Snapshot",
        value=_format_role_id_counts(current_counts) or "No role-size rows.",
        inline=False,
    )
    embed.set_footer(
        text=(
            "Source: RoleSize snapshots; values carry forward from last known "
            "snapshot."
        )
    )
    return embed, file


def _plot_overview(summary: OverviewSummary) -> None:
    labels = [
        bucket_label(bucket.start, summary.filters.time_range.bucket)
        for bucket in summary.bucket_series
    ]
    voyages = [bucket.voyages for bucket in summary.bucket_series]
    hosted = [bucket.hosted for bucket in summary.bucket_series]
    positions = range(len(labels))
    tick_step = max(1, len(labels) // 18)
    sparse_labels = [
        label if index % tick_step == 0 else "" for index, label in enumerate(labels)
    ]

    figure, axis = plt.subplots(figsize=(14, 7))
    axis.bar(
        positions, voyages, label="Voyage attendances", color="#4C78A8", alpha=0.55
    )
    axis.plot(
        list(positions),
        hosted,
        label="Hosted voyages",
        color="#F58518",
        marker="o",
        linewidth=2,
    )
    axis.set_title(
        "Voyage Activity "
        f"({summary.filters.time_range.label}, "
        f"{summary.filters.time_range.bucket} buckets)"
    )
    axis.set_ylabel("Count")
    axis.set_xticks(list(positions))
    axis.set_xticklabels(sparse_labels, rotation=45, ha="right", fontsize=8)
    axis.grid(axis="y", linestyle="--", alpha=0.25)
    axis.legend(loc="upper left")
    figure.tight_layout()


def _plot_ship_activity(summary) -> None:
    labels = [
        bucket_label(bucket.start, summary.filters.time_range.bucket)
        for bucket in summary.bucket_series
    ]
    hosted = [bucket.hosted for bucket in summary.bucket_series]
    voyages = [bucket.voyages for bucket in summary.bucket_series]
    positions = range(len(labels))
    tick_step = max(1, len(labels) // 18)
    sparse_labels = [
        label if index % tick_step == 0 else "" for index, label in enumerate(labels)
    ]
    figure, axis = plt.subplots(figsize=(14, 7))
    axis.bar(
        positions,
        voyages,
        label="Voyage attendances",
        color="#4C78A8",
        alpha=0.5,
    )
    axis.plot(
        list(positions),
        hosted,
        label="Hosted voyages",
        color="#F58518",
        marker="o",
    )
    axis.set_title("Ship Activity")
    axis.set_ylabel("Count")
    axis.set_xticks(list(positions))
    axis.set_xticklabels(sparse_labels, rotation=45, ha="right", fontsize=8)
    axis.grid(axis="y", linestyle="--", alpha=0.25)
    axis.legend(loc="upper left")
    figure.tight_layout()


def _plot_ping_summary(summary) -> None:
    labels = [
        bucket_label(bucket.start, summary.filters.time_range.bucket)
        for bucket in summary.bucket_series
    ]
    vp = [bucket.vp_enabled for bucket in summary.bucket_series]
    non_vp = [bucket.non_vp for bucket in summary.bucket_series]
    positions = range(len(labels))
    tick_step = max(1, len(labels) // 18)
    sparse_labels = [
        label if index % tick_step == 0 else "" for index, label in enumerate(labels)
    ]
    figure, axis = plt.subplots(figsize=(14, 7))
    axis.bar(positions, vp, label="VP enabled", color="#54A24B", alpha=0.85)
    axis.bar(positions, non_vp, bottom=vp, label="Non-VP", color="#E45756", alpha=0.85)
    axis.set_title("Ping Usage")
    axis.set_ylabel("Pings")
    axis.set_xticks(list(positions))
    axis.set_xticklabels(sparse_labels, rotation=45, ha="right", fontsize=8)
    axis.grid(axis="y", linestyle="--", alpha=0.25)
    axis.legend(loc="upper left")
    figure.tight_layout()


def _plot_role_size_summary(summary) -> None:
    labels = [
        bucket_label(bucket, summary.filters.time_range.bucket)
        for bucket in summary.filters.time_range.buckets
    ]
    positions = range(len(labels))
    tick_step = max(1, len(labels) // 18)
    sparse_labels = [
        label if index % tick_step == 0 else "" for index, label in enumerate(labels)
    ]
    figure, axis = plt.subplots(figsize=(14, 7))
    for role_id, points in summary.series.items():
        axis.plot(
            list(positions),
            [point.member_count for point in points],
            marker="o",
            linewidth=2,
            label=_rank_label_for_role_id(role_id),
        )
    axis.set_title("Rank Size")
    axis.set_ylabel("Members")
    axis.set_xticks(list(positions))
    axis.set_xticklabels(sparse_labels, rotation=45, ha="right", fontsize=8)
    axis.grid(axis="y", linestyle="--", alpha=0.25)
    axis.legend(loc="upper left", fontsize=8)
    figure.tight_layout()


def _plot_rank_share(rank_share: RankShare) -> None:
    names = list(rank_share.rank_counts.keys()) or ["No data"]
    counts = list(rank_share.rank_counts.values()) or [0]
    figure, axis = plt.subplots(figsize=(12, 7))
    axis.barh(names[::-1], counts[::-1], color="#4C78A8")
    axis.set_title("Voyage Participant Rank Share")
    axis.set_xlabel("Voyage rows")
    axis.grid(axis="x", linestyle="--", alpha=0.25)
    figure.tight_layout()


def _plot_companions(companion_share: CompanionShare) -> None:
    labels = [str(user_id) for user_id, _ in companion_share.companion_counts] or [
        "No data"
    ]
    counts = [count for _, count in companion_share.companion_counts] or [0]
    figure, axis = plt.subplots(figsize=(12, 7))
    axis.bar(range(len(labels)), counts, color="#54A24B")
    axis.set_title("Top Voyage Companions")
    axis.set_ylabel("Shared voyages")
    axis.set_xticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axis.grid(axis="y", linestyle="--", alpha=0.25)
    figure.tight_layout()


def _filter_description(
        filters: AnalyticsFilters,
        ship: discord.Role | None,
        user: discord.Member | None,
) -> str:
    start_text = (
        "beginning of records"
        if filters.time_range.start is None
        else f"{filters.time_range.start:%Y-%m-%d %H:%M} UTC"
    )
    range_line = (
        f"Range: **{filters.time_range.label}** "
        f"({start_text} to "
        f"{filters.time_range.end:%Y-%m-%d %H:%M} UTC), "
        f"bucketed by **{filters.time_range.bucket}**."
    )
    filter_bits = [
        _ship_filter_text(filters.ship_role_id, ship),
        _user_filter_text(filters.user_id, user),
        f"Voyage type: **{filters.voyage_type.value}**"
        if filters.voyage_type
        else "Voyage type: **All**",
    ]
    return f"{range_line}\n" + " | ".join(filter_bits)


def _ship_filter_text(
        ship_role_id: int | None,
        ship: discord.Role | None,
) -> str:
    if ship:
        return f"Ship: **{ship.name}**"
    if ship_role_id:
        return f"Ship: **{_ship_label(ship_role_id)}**"
    return "Ship: **All ships**"


def _user_filter_text(
        user_id: int | None,
        user: discord.Member | None,
) -> str:
    if user:
        return f"User: **{user.display_name}**"
    if user_id:
        return f"User: **<@{user_id}>**"
    return "User: **All users**"


def _data_integrity_footer(filters: AnalyticsFilters) -> str:
    base = "Source: persisted Hosted, Voyages, Subclasses, Sailor, and Rank rows."
    if filters.has_user_filter:
        base += " User filter uses persisted target_id/host_id attribution."
    base += (
        " Rank analytics prefer voyage-time stored ranks; current Sailor rank is "
        "fallback only."
    )
    return base


def _format_user_counts(rows) -> str:
    return "\n".join(
        f"{index}. <@{user_id}> — **{count}**"
        for index, (user_id, count) in enumerate(rows, start=1)
    )


def _format_user_counts_with_percent(rows, denominator: int) -> str:
    return "\n".join(
        (
            f"{index}. <@{user_id}> — **{count}**"
            f"{_percent_suffix(count, denominator)}"
        )
        for index, (user_id, count) in enumerate(rows, start=1)
    )


def _format_ship_counts(rows) -> str:
    return "\n".join(
        f"{index}. {_ship_label(role_id)} — **{count}**"
        for index, (role_id, count) in enumerate(rows, start=1)
    )


def _format_ship_counts_with_percent(rows, denominator: int) -> str:
    return "\n".join(
        (
            f"{index}. {_ship_label(role_id)} "
            f"— **{count}**{_percent_suffix(count, denominator)}"
        )
        for index, (role_id, count) in enumerate(rows, start=1)
    )


def _format_pair_counts_with_percent(rows, denominator: int) -> str:
    return "\n".join(
        (
            f"{index}. <@{user_one_id}> + <@{user_two_id}> — **{count}**"
            f"{_percent_suffix(count, denominator)}"
        )
        for index, ((user_one_id, user_two_id), count) in enumerate(rows, start=1)
    )


def _format_ship_pair_counts_with_percent(rows, denominator: int) -> str:
    return "\n".join(
        (
            f"{index}. {_ship_label(ship_one_role_id)} + "
            f"{_ship_label(ship_two_role_id)} — **{count}**"
            f"{_percent_suffix(count, denominator)}"
        )
        for index, ((ship_one_role_id, ship_two_role_id), count) in enumerate(
            rows,
            start=1,
        )
    )


def _format_ship_pairing_counts_with_percent(rows, denominator: int) -> str:
    return "\n".join(
        (
            f"{index}. {' + '.join(_ship_label(role_id) for role_id in role_ids)} "
            f"— **{count}**{_percent_suffix(count, denominator)}"
        )
        for index, (role_ids, count) in enumerate(rows, start=1)
    )


def _ship_label(role_id: int) -> str:
    if role_id in SHIP_LABEL_BY_ROLE_ID:
        return SHIP_LABEL_BY_ROLE_ID[role_id]
    return f"Unknown ship ({role_id})"


def _format_enum_counts(counts: dict) -> str:
    rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return "\n".join(
        f"{key.value if hasattr(key, 'value') else key}: **{value}**"
        for key, value in rows
    )


def _format_named_counts(counts: dict[str, int]) -> str:
    rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return "\n".join(f"{name}: **{count}**" for name, count in rows[:12])


def _format_named_counts_with_percent(counts: dict[str, int], denominator: int) -> str:
    rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return "\n".join(
        f"{name}: **{count}**{_percent_suffix(count, denominator)}"
        for name, count in rows[:12]
    )


def _percent_suffix(count: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    return f" ({count / denominator:.1%})"


def _overview_cache_payload(summary: OverviewSummary) -> dict:
    return {
        "section": "overview",
        "filters": _filter_cache_payload(summary.filters),
        "series": [
            {
                "start": bucket.start.isoformat(),
                "voyages": bucket.voyages,
                "hosted": bucket.hosted,
            }
            for bucket in summary.bucket_series
        ],
        "totals": {
            "voyages": summary.total_voyages,
            "hosted": summary.total_hosted,
            "logs": summary.unique_voyage_logs,
        },
    }


def _filter_cache_payload(filters: AnalyticsFilters) -> dict:
    return {
        "range": filters.time_range.label,
        "start": _time_range_start_cache_value(filters.time_range.start),
        "end": filters.time_range.end.isoformat(),
        "bucket": filters.time_range.bucket,
        "ship_role_id": filters.ship_role_id,
        "user_id": filters.user_id,
        "voyage_type": filters.voyage_type.value if filters.voyage_type else None,
    }


def _ship_filter_description(filters) -> str:
    bits = [
        (
            f"Range: **{filters.time_range.label}**, bucketed by "
            f"**{filters.time_range.bucket}**"
        ),
        (
            "Ship role: **"
            f"{_ship_label(filters.ship_role_id)}"
            "**"
            if filters.ship_role_id
            else "Ship role: **All**"
        ),
    ]
    if filters.fleet_role_ids:
        bits.append(f"Fleet roles: **{len(filters.fleet_role_ids)} ships**")
    if filters.ship_name:
        bits.append(f"Ship name: **{filters.ship_name}**")
    if filters.host_id:
        bits.append(f"Host: **<@{filters.host_id}>**")
    if filters.crew_member_id:
        bits.append(f"Crew member: **<@{filters.crew_member_id}>**")
    if filters.voyage_type:
        bits.append(f"Voyage type: **{filters.voyage_type.value}**")
    else:
        bits.append("Voyage type: **All**")
    return " | ".join(bits)


def _ping_filter_description(filters) -> str:
    bits = [
        (
            f"Range: **{filters.time_range.label}**, bucketed by "
            f"**{filters.time_range.bucket}**"
        ),
        (
            f"Ping role: **<@&{filters.ping_role_id}>**"
            if filters.ping_role_id
            else "Ping role: **All**"
        ),
        (
            "Ship: **"
            f"{_ship_label(filters.ship_role_id)}"
            "**"
            if filters.ship_role_id
            else "Ship: **All**"
        ),
    ]
    if filters.user_id:
        bits.append(f"User: **<@{filters.user_id}>**")
    if filters.has_vp_permission is True:
        bits.append("VP status: **VP enabled**")
    elif filters.has_vp_permission is False:
        bits.append("VP status: **Non-VP**")
    else:
        bits.append("VP status: **All**")
    return " | ".join(bits)


def _ship_filter_cache_payload(filters) -> dict:
    return {
        "range": filters.time_range.label,
        "start": _time_range_start_cache_value(filters.time_range.start),
        "end": filters.time_range.end.isoformat(),
        "bucket": filters.time_range.bucket,
        "ship_role_id": filters.ship_role_id,
        "fleet_role_ids": list(filters.fleet_role_ids),
        "ship_name": filters.ship_name,
        "host_id": filters.host_id,
        "crew_member_id": filters.crew_member_id,
        "voyage_type": filters.voyage_type.value if filters.voyage_type else None,
    }


def _ping_filter_cache_payload(filters) -> dict:
    return {
        "range": filters.time_range.label,
        "start": _time_range_start_cache_value(filters.time_range.start),
        "end": filters.time_range.end.isoformat(),
        "bucket": filters.time_range.bucket,
        "ping_role_id": filters.ping_role_id,
        "ship_role_id": filters.ship_role_id,
        "user_id": filters.user_id,
        "has_vp_permission": filters.has_vp_permission,
    }


def _time_range_start_cache_value(start: datetime | None) -> str | None:
    return start.isoformat() if start is not None else None


def _format_ship_activity_rows(rows) -> str:
    sorted_rows = sorted(
        rows,
        key=lambda row: (row.hosted + row.voyages, row.hosted),
        reverse=True,
    )
    return "\n".join(
        f"{index}. "
        f"{_ship_label(row.ship_role_id)} "
        f"- hosted **{row.hosted}**, voyages **{row.voyages}**"
        for index, row in enumerate(sorted_rows[:12], start=1)
    )


def _format_role_id_counts(counts: dict[int, int]) -> str:
    rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return "\n".join(
        f"{_rank_label_for_role_id(role_id)}: **{count}**"
        for role_id, count in rows[:12]
    )


def _rank_label_for_role_id(role_id: int) -> str:
    for rank in RANKS:
        if role_id in rank.role_ids:
            return f"{rank.identifier} {rank.name}"
    return f"<@&{role_id}>"


def _rank_role_ids(rank_group: str, rank_identifier: str | None) -> list[int]:
    role_ids: list[int] = []
    for rank in RANKS:
        if rank_identifier and rank.identifier.lower() != rank_identifier.lower():
            continue
        if rank_identifier is None and not _rank_in_group(rank, rank_group):
            continue
        role_ids.extend(rank.role_ids)
    return role_ids


def _rank_in_group(rank, rank_group: str) -> bool:
    if rank_group == "all":
        return rank.name != "Dungeon Master"
    if rank_group == "active" and rank.name in INACTIVE_RANK_NAMES:
        return False
    if rank_group == "e3_up" and rank.index < 3:
        return False
    if rank_group == "nco_up" and rank.index < 4:
        return False
    if rank_group == "snco_up" and rank.index < 6:
        return False
    if rank_group == "officer" and rank.index < 9:
        return False
    return not (rank_group != "all" and rank.name == "Dungeon Master")


def _vp_status_filter(value: str) -> bool | None:
    if value == "vp":
        return True
    if value == "non_vp":
        return False
    return None


async def _validate_ship_filter(
        interaction: discord.Interaction,
        ship: discord.Role | None,
) -> bool:
    if ship is None or ship.id in SHIP_ROLE_IDS:
        return True
    await interaction.followup.send(
        embed=error_embed(
            title="Invalid ship filter",
            description="The ship filter must be one of the configured ship roles.",
            footer=False,
        ),
        ephemeral=True,
    )
    return False


async def _validate_ping_role_filter(
        interaction: discord.Interaction,
        ping_role: discord.Role | None,
) -> bool:
    if ping_role is None or ping_role.id in TRACKED_PING_ROLE_IDS:
        return True
    await interaction.followup.send(
        embed=error_embed(
            title="Invalid ping role filter",
            description=(
                "The ping role filter must be one of the configured tracked "
                "ping roles."
            ),
            footer=False,
        ),
        ephemeral=True,
    )
    return False


async def _send_unavailable(
        interaction: discord.Interaction,
        title: str,
) -> None:
    await interaction.followup.send(
        embed=error_embed(
            title=title,
            description="Unable to build the analytics report right now.",
            footer=False,
        ),
        ephemeral=True,
    )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AnalyticsHub(bot))
