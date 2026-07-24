from __future__ import annotations

import asyncio
import io
import logging
import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from itertools import groupby

import discord
from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle

from src.briefings.message import BriefingMessage, chunk_discord_embeds
from src.config import BOA_ROLE
from src.config.briefings import (
    BRIEFING_HOSTING_REQUIREMENT_DAYS,
    BRIEFING_VOYAGE_REQUIREMENT_DAYS,
    DAILY_AVATAR_FETCH_TIMEOUT_SECONDS,
    DAILY_AVATAR_SIZE,
    DAILY_HOSTING_DUE_SOON_DAYS,
    DAILY_VOYAGE_DUE_SOON_DAYS,
    HOST_CAPABLE_ROLE_IDS,
)
from src.data.repository.ship_briefing_repository import ShipBriefingRepository
from src.data.structs import SailorCO
from src.utils.check_awards import PendingShipAward, get_pending_ship_awards
from src.utils.image_cache import render_matplotlib_plot_to_png

MAX_ATTENTION_ROWS_PER_IMAGE = 18
MAX_AWARDS_PER_EMBED = 10
MAX_EMBED_FIELDS = 25
MAX_EMBED_FIELD_VALUE = 1024

BACKGROUND = "#111a1f"
PANEL = "#1b262c"
TEXT = "#edf2f4"
MUTED = "#93a4aa"
RED = "#ef3340"
AMBER = "#f4a900"
GREEN = "#2bd673"
TRACK = "#34434a"
BLUE = "#4c8dff"
GREY = "#718087"

log = logging.getLogger(__name__)


class ChaseStatus(StrEnum):
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"


@dataclass(frozen=True)
class ChaseEntry:
    sailor_id: int
    sailor_name: str
    status: ChaseStatus
    days: int
    missing_history: bool = False
    on_loa: bool = False


@dataclass(frozen=True)
class SailorAvatar:
    sailor_id: int
    png: bytes


@dataclass(frozen=True)
class AttentionRequirement:
    label: str
    entry: ChaseEntry

    @property
    def is_loa_overdue(self) -> bool:
        return self.entry.status == ChaseStatus.OVERDUE and self.entry.on_loa


@dataclass(frozen=True)
class AttentionRow:
    sailor_id: int
    sailor_name: str
    requirements: tuple[AttentionRequirement, ...]

    @property
    def is_overdue(self) -> bool:
        return any(
            requirement.entry.status == ChaseStatus.OVERDUE
            and not requirement.is_loa_overdue
            for requirement in self.requirements
        )

    @property
    def is_loa_only(self) -> bool:
        return not self.is_overdue and any(
            requirement.is_loa_overdue for requirement in self.requirements
        )


@dataclass(frozen=True)
class ActionItem:
    sailor_id: int
    sailor_name: str
    label: str
    detail: str
    responsible_id: int | None
    responsible_name: str | None = None


@dataclass(frozen=True)
class DailyShipBriefing:
    ship_role_id: int
    ship_name: str
    reference_time: datetime
    voyage_due_soon: int
    voyage_overdue: int
    voyage_current: int
    hosting_due_soon: int
    hosting_overdue: int
    hosting_current: int
    voyage_chase: tuple[ChaseEntry, ...]
    hosting_chase: tuple[ChaseEntry, ...]
    pending_awards: tuple[PendingShipAward, ...]
    requirement_actions: tuple[ActionItem, ...]
    award_actions: tuple[ActionItem, ...]
    avatars: tuple[SailorAvatar, ...] = ()

    @property
    def due_soon_count(self) -> int:
        return self.voyage_due_soon + self.hosting_due_soon

    @property
    def overdue_count(self) -> int:
        return (
            self.voyage_overdue
            + self.hosting_overdue
            - self.loa_voyage_overdue_count
            - self.loa_hosting_overdue_count
        )

    @property
    def loa_voyage_overdue_count(self) -> int:
        return sum(
            entry.status == ChaseStatus.OVERDUE and entry.on_loa
            for entry in self.voyage_chase
        )

    @property
    def loa_hosting_overdue_count(self) -> int:
        return sum(
            entry.status == ChaseStatus.OVERDUE and entry.on_loa
            for entry in self.hosting_chase
        )

    @property
    def action_count(self) -> int:
        return len(self.requirement_actions) + len(self.award_actions)

    def action_count_for(self, concerns: Mapping[str, bool]) -> int:
        return len(
            _enabled_actions(
                self,
                requirements_enabled=concerns.get("requirements", False),
                awards_enabled=concerns.get("awards", False),
            )
        )


def build_daily_briefing(
    repository: ShipBriefingRepository,
    *,
    guild: discord.Guild,
    ship_role,
    ship_name: str,
    reference_time: datetime,
) -> DailyShipBriefing:
    reference_time = _ensure_utc(reference_time)
    members = list(ship_role.members)
    member_ids = [member.id for member in members]
    sailors = {
        sailor.discord_id: sailor
        for sailor in repository.get_sailors_by_ids(member_ids)
    }
    voyage_activity = repository.get_latest_voyage_activity(member_ids)
    hosting_activity = repository.get_latest_hosting_activity(member_ids)
    role_additions = repository.get_latest_ship_role_additions(
        ship_role_id=ship_role.id,
        sailor_ids=member_ids,
    )
    public_service_counts = repository.get_public_service_counts(member_ids)

    voyage_chase: list[ChaseEntry] = []
    hosting_chase: list[ChaseEntry] = []
    voyage_current = 0
    hosting_current = 0
    pending_awards: list[PendingShipAward] = []
    requirement_actions: list[ActionItem] = []
    award_actions: list[ActionItem] = []

    for member in members:
        baseline = _member_baseline(
            member,
            role_additions.get(member.id),
            reference_time,
        )
        voyage_entry = classify_activity(
            member=member,
            activity_at=voyage_activity.get(member.id),
            baseline_at=baseline,
            requirement_days=BRIEFING_VOYAGE_REQUIREMENT_DAYS,
            due_soon_days=DAILY_VOYAGE_DUE_SOON_DAYS,
            reference_time=reference_time,
        )
        if voyage_entry is None:
            voyage_current += 1
        else:
            voyage_chase.append(voyage_entry)
            if voyage_entry.status == ChaseStatus.OVERDUE and not _member_is_on_loa(
                member
            ):
                responsible_id = _acting_officer_id(member, guild)
                requirement_actions.append(
                    ActionItem(
                        sailor_id=member.id,
                        sailor_name=member.display_name,
                        label="Voyaging",
                        detail=_chase_age(voyage_entry),
                        responsible_id=responsible_id,
                        responsible_name=_responsible_name(
                            guild,
                            responsible_id,
                        ),
                    )
                )

        if member_can_host(member):
            hosting_entry = classify_activity(
                member=member,
                activity_at=hosting_activity.get(member.id),
                baseline_at=baseline,
                requirement_days=BRIEFING_HOSTING_REQUIREMENT_DAYS,
                due_soon_days=DAILY_HOSTING_DUE_SOON_DAYS,
                reference_time=reference_time,
            )
            if hosting_entry is None:
                hosting_current += 1
            else:
                hosting_chase.append(hosting_entry)
                if (
                    hosting_entry.status == ChaseStatus.OVERDUE
                    and not _member_is_on_loa(member)
                ):
                    responsible_id = _acting_officer_id(member, guild)
                    requirement_actions.append(
                        ActionItem(
                            sailor_id=member.id,
                            sailor_name=member.display_name,
                            label="Hosting",
                            detail=_chase_age(hosting_entry),
                            responsible_id=responsible_id,
                            responsible_name=_responsible_name(
                                guild,
                                responsible_id,
                            ),
                        )
                    )

        sailor = sailors.get(member.id)
        is_boa = BOA_ROLE in {role.id for role in member.roles}
        if sailor is None or is_boa:
            continue

        awards = get_pending_ship_awards(
            guild,
            sailor,
            member,
            public_service_count=public_service_counts.get(member.id, 0),
        )
        pending_awards.extend(awards)
        award_actions.extend(
            ActionItem(
                sailor_id=member.id,
                sailor_name=member.display_name,
                label="Award",
                detail=award.award_name,
                responsible_id=award.responsible_id,
                responsible_name=award.responsible_name,
            )
            for award in awards
        )

    voyage_chase.sort(key=_chase_sort_key)
    hosting_chase.sort(key=_chase_sort_key)
    return DailyShipBriefing(
        ship_role_id=ship_role.id,
        ship_name=ship_name,
        reference_time=reference_time,
        voyage_due_soon=_count_status(voyage_chase, ChaseStatus.DUE_SOON),
        voyage_overdue=_count_status(voyage_chase, ChaseStatus.OVERDUE),
        voyage_current=voyage_current,
        hosting_due_soon=_count_status(hosting_chase, ChaseStatus.DUE_SOON),
        hosting_overdue=_count_status(hosting_chase, ChaseStatus.OVERDUE),
        hosting_current=hosting_current,
        voyage_chase=tuple(voyage_chase),
        hosting_chase=tuple(hosting_chase),
        pending_awards=tuple(pending_awards),
        requirement_actions=tuple(requirement_actions),
        award_actions=tuple(award_actions),
    )


async def enrich_daily_briefing_avatars(
    briefing: DailyShipBriefing,
    *,
    members: Sequence,
    timeout_seconds: float = DAILY_AVATAR_FETCH_TIMEOUT_SECONDS,
) -> DailyShipBriefing:
    sailor_ids = {
        entry.sailor_id for entry in (*briefing.hosting_chase, *briefing.voyage_chase)
    }
    members_by_id = {member.id: member for member in members if member.id in sailor_ids}

    async def fetch(member) -> SailorAvatar | None:
        try:
            asset = member.display_avatar.replace(
                size=DAILY_AVATAR_SIZE,
                format="png",
                static_format="png",
            )
            png = await asyncio.wait_for(
                asset.read(),
                timeout=timeout_seconds,
            )
            return SailorAvatar(sailor_id=member.id, png=png)
        except Exception:
            log.warning(
                "Daily briefing avatar unavailable; using initials.",
                extra={"sailor": member.id},
                exc_info=True,
            )
            return None

    results = await asyncio.gather(
        *(fetch(member) for member in members_by_id.values())
    )
    avatars = tuple(result for result in results if result is not None)
    return replace(briefing, avatars=avatars)


def build_attention_rows(
    briefing: DailyShipBriefing,
) -> tuple[AttentionRow, ...]:
    grouped: defaultdict[int, list[AttentionRequirement]] = defaultdict(list)
    names: dict[int, str] = {}
    for label, entries in (
        ("Hosting", briefing.hosting_chase),
        ("Voyaging", briefing.voyage_chase),
    ):
        for entry in entries:
            names[entry.sailor_id] = entry.sailor_name
            grouped[entry.sailor_id].append(
                AttentionRequirement(label=label, entry=entry)
            )

    rows = [
        AttentionRow(
            sailor_id=sailor_id,
            sailor_name=names[sailor_id],
            requirements=tuple(
                sorted(
                    requirements,
                    key=lambda requirement: (
                        requirement.entry.status != ChaseStatus.OVERDUE,
                        requirement.label,
                    ),
                )
            ),
        )
        for sailor_id, requirements in grouped.items()
    ]
    rows.sort(key=_attention_sort_key)
    return tuple(rows)


def compose_daily_briefing_messages(
    briefing: DailyShipBriefing,
    *,
    concerns: Mapping[str, bool],
    mentions_enabled: bool,
) -> tuple[BriefingMessage, ...]:
    requirements_enabled = concerns.get("requirements", False)
    awards_enabled = concerns.get("awards", False)
    sections: list[tuple[discord.Embed, discord.File | None]] = []

    if requirements_enabled:
        images = render_daily_dashboard_images(
            briefing,
            include_awards=awards_enabled,
        )
        for page, image in enumerate(images, start=1):
            filename = f"daily_briefing_{briefing.ship_role_id}_{page}.png"
            embed = discord.Embed(
                title=(
                    f"Daily briefing · {briefing.ship_name}"
                    if page == 1
                    else f"Attention continued · {briefing.ship_name}"
                ),
                description=(
                    _situation_summary(
                        briefing,
                        awards_enabled=awards_enabled,
                    )
                    if page == 1
                    else None
                ),
                color=_daily_color(
                    briefing,
                    include_awards=awards_enabled,
                ),
            )
            embed.set_image(url=f"attachment://{filename}")
            sections.append(
                (
                    embed,
                    discord.File(io.BytesIO(image), filename=filename),
                )
            )

    if awards_enabled:
        sections.extend(
            (embed, None)
            for embed in render_pending_award_embeds(
                briefing.pending_awards,
                subject_name=briefing.ship_name,
            )
        )

    messages = list(_pack_situation_messages(sections))

    actions = _enabled_actions(
        briefing,
        requirements_enabled=requirements_enabled,
        awards_enabled=awards_enabled,
    )
    if actions:
        messages.extend(
            build_tasking_messages(
                actions,
                ship_name=briefing.ship_name,
                mentions_enabled=mentions_enabled,
            )
        )

    return tuple(messages)


def classify_activity(
    *,
    member,
    activity_at: datetime | None,
    baseline_at: datetime,
    requirement_days: int,
    due_soon_days: int,
    reference_time: datetime,
) -> ChaseEntry | None:
    missing_history = activity_at is None
    anchor = baseline_at if missing_history else _ensure_utc(activity_at)
    threshold_at = anchor + timedelta(days=requirement_days)
    seconds_until_due = (threshold_at - reference_time).total_seconds()
    if seconds_until_due < 0:
        days = (
            max(
                0,
                math.floor((reference_time - baseline_at).total_seconds() / 86400),
            )
            if missing_history
            else max(1, math.ceil(abs(seconds_until_due) / 86400))
        )
        return ChaseEntry(
            sailor_id=member.id,
            sailor_name=member.display_name,
            status=ChaseStatus.OVERDUE,
            days=days,
            missing_history=missing_history,
            on_loa=_member_is_on_loa(member),
        )
    days_remaining = math.ceil(seconds_until_due / 86400)
    if days_remaining <= due_soon_days:
        days = (
            max(
                0,
                math.floor((reference_time - baseline_at).total_seconds() / 86400),
            )
            if missing_history
            else max(0, days_remaining)
        )
        return ChaseEntry(
            sailor_id=member.id,
            sailor_name=member.display_name,
            status=ChaseStatus.DUE_SOON,
            days=days,
            missing_history=missing_history,
            on_loa=_member_is_on_loa(member),
        )
    return None


def member_can_host(member) -> bool:
    return bool({role.id for role in member.roles}.intersection(HOST_CAPABLE_ROLE_IDS))


def render_daily_dashboard_images(
    briefing: DailyShipBriefing,
    *,
    include_awards: bool = True,
) -> tuple[bytes, ...]:
    rows = build_attention_rows(briefing)
    pages = [
        rows[index : index + MAX_ATTENTION_ROWS_PER_IMAGE]
        for index in range(0, len(rows), MAX_ATTENTION_ROWS_PER_IMAGE)
    ] or [[]]
    return tuple(
        _render_requirements_page(
            briefing,
            rows=page_rows,
            page=page,
            page_count=len(pages),
            include_awards=include_awards,
        )
        for page, page_rows in enumerate(pages, start=1)
    )


def build_tasking_messages(
    actions: tuple[ActionItem, ...],
    *,
    ship_name: str,
    mentions_enabled: bool = True,
) -> tuple[BriefingMessage, ...]:
    grouped_actions: defaultdict[int | None, list[ActionItem]] = defaultdict(list)
    for action in actions:
        grouped_actions[action.responsible_id].append(action)

    mention_format = "<@{}>" if mentions_enabled else "@<{}>"
    officer_ids = sorted(
        grouped_actions,
        key=lambda officer_id: (
            officer_id is None,
            officer_id if officer_id is not None else 0,
        ),
    )
    fields: list[tuple[str, str]] = []
    for officer_id in officer_ids:
        owned_actions = grouped_actions[officer_id]
        owner = (
            _task_owner_name(owned_actions, officer_id)
            if officer_id is not None
            else "Unassigned"
        )
        field_name = (
            f"{owner} · {len(owned_actions)} action"
            f"{'s' if len(owned_actions) != 1 else ''}"
        )
        value_chunks = _chunk_tasking_lines(
            _tasking_lines(
                tuple(owned_actions),
                mentions_enabled=mentions_enabled,
            ),
            max_length=MAX_EMBED_FIELD_VALUE,
        )
        for chunk_index, value in enumerate(value_chunks, start=1):
            name = field_name
            if len(value_chunks) > 1:
                name += f" · {chunk_index}/{len(value_chunks)}"
            fields.append((name, value))

    embed_pages = [
        fields[index : index + MAX_EMBED_FIELDS]
        for index in range(0, len(fields), MAX_EMBED_FIELDS)
    ]
    embeds = []
    for page, page_fields in enumerate(embed_pages, start=1):
        title = f"Officer tasking · {ship_name}"
        if len(embed_pages) > 1:
            title += f" · {page}/{len(embed_pages)}"
        embed = discord.Embed(
            title=title,
            description=(
                f"**{len(actions)} action"
                f"{'s' if len(actions) != 1 else ''}** · "
                "overdue requirements and pending awards"
            ),
            color=discord.Color.blue(),
        )
        for name, value in page_fields:
            embed.add_field(name=name, value=value, inline=False)
        embeds.append(embed)

    messages = []
    for embed_page in chunk_discord_embeds(embeds):
        messages.append(
            BriefingMessage(
                embeds=embed_page,
            )
        )
    assigned_mentions = [
        mention_format.format(officer_id)
        for officer_id in officer_ids
        if officer_id is not None
    ]
    reminder = (
        f"Your daily briefing is ready, {' '.join(assigned_mentions)}.\n"
        "Please review the assigned actions above."
        if assigned_mentions
        else ("Your daily briefing is ready.\nUnassigned actions require review.")
    )
    messages.append(
        BriefingMessage(
            content=reminder,
            allow_user_mentions=mentions_enabled,
        )
    )
    return tuple(messages)


def _render_requirements_page(
    briefing: DailyShipBriefing,
    *,
    rows: Sequence[AttentionRow],
    page: int,
    page_count: int,
    include_awards: bool,
) -> bytes:
    first_page = page == 1
    section_count = len({_attention_section(row) for row in rows})
    height = max(
        4.8,
        1.35 + (2.75 if first_page else 0.0) + len(rows) * 0.48 + section_count * 0.35,
    )
    avatars = {avatar.sailor_id: avatar.png for avatar in briefing.avatars}

    def plotter() -> None:
        figure = plt.figure(figsize=(8, height), dpi=150, facecolor=BACKGROUND)
        axes = figure.add_axes((0, 0, 1, 1))
        axes.set_facecolor(BACKGROUND)
        axes.set_xlim(0, 1)
        axes.set_ylim(0, 1)
        axes.axis("off")
        unit = 1 / height
        y = 0.95

        axes.text(
            0.04,
            y,
            briefing.ship_name,
            color=TEXT,
            fontsize=17,
            fontweight="bold",
            va="top",
        )
        axes.text(
            0.04,
            y - 0.32 * unit,
            (
                "DAILY BRIEFING · "
                f"{briefing.reference_time.strftime('%d %b %Y').upper()} · "
                f"{briefing.reference_time.strftime('%A').upper()}"
            ),
            color=MUTED,
            fontsize=8.5,
            fontweight="bold",
            va="top",
        )
        if page_count > 1:
            axes.text(
                0.96,
                y,
                f"PAGE {page}/{page_count}",
                color=MUTED,
                fontsize=8.5,
                fontweight="bold",
                ha="right",
                va="top",
            )
        y -= 0.78 * unit

        if first_page:
            axes.text(
                0.04,
                y,
                "COMMAND STATUS",
                color=MUTED,
                fontsize=10,
                fontweight="bold",
                va="top",
            )
            y -= 0.34 * unit
            y = _draw_status_cards(
                axes,
                briefing=briefing,
                y=y,
                unit=unit,
                include_awards=include_awards,
            )
            axes.text(
                0.04,
                y,
                "REQUIREMENT PRESSURE",
                color=MUTED,
                fontsize=10,
                fontweight="bold",
                va="top",
            )
            y -= 0.34 * unit
            y = _draw_pressure_bar(
                axes,
                y=y,
                label="Hosting",
                overdue=(briefing.hosting_overdue - briefing.loa_hosting_overdue_count),
                due_soon=briefing.hosting_due_soon,
                current=briefing.hosting_current,
                on_loa=briefing.loa_hosting_overdue_count,
                unit=unit,
            )
            y = _draw_pressure_bar(
                axes,
                y=y,
                label="Voyaging",
                overdue=(briefing.voyage_overdue - briefing.loa_voyage_overdue_count),
                due_soon=briefing.voyage_due_soon,
                current=briefing.voyage_current,
                on_loa=briefing.loa_voyage_overdue_count,
                unit=unit,
            )

        axes.text(
            0.04,
            y,
            "NEEDS ATTENTION",
            color=MUTED,
            fontsize=10,
            fontweight="bold",
            va="top",
        )
        axes.text(
            0.96,
            y,
            f"{len(rows)} sailor{'s' if len(rows) != 1 else ''}",
            color=MUTED,
            fontsize=8.5,
            ha="right",
            va="top",
        )
        y -= 0.36 * unit

        if not rows:
            _draw_all_clear(axes, y=y, unit=unit)
            return

        last_section = None
        for row in rows:
            section = _attention_section(row)
            if section != last_section:
                section_size = sum(
                    _attention_section(candidate) == section for candidate in rows
                )
                axes.text(
                    0.04,
                    y,
                    f"{section} · {section_size}",
                    color=MUTED,
                    fontsize=9,
                    fontweight="bold",
                    va="top",
                )
                y -= 0.30 * unit
                last_section = section
            _draw_attention_row(
                axes,
                row,
                avatar_png=avatars.get(row.sailor_id),
                y=y,
                unit=unit,
                figure_height=height,
            )
            y -= 0.46 * unit

    return render_matplotlib_plot_to_png(plotter)


def _draw_status_cards(
    axes,
    *,
    briefing: DailyShipBriefing,
    y: float,
    unit: float,
    include_awards: bool,
) -> float:
    cards = [
        ("OVERDUE", briefing.overdue_count, RED),
        ("DUE SOON", briefing.due_soon_count, AMBER),
    ]
    award_count = len(briefing.pending_awards) if include_awards else 0
    action_count = len(briefing.requirement_actions)
    if include_awards:
        cards.append(("AWARDS", award_count, "#e5bd45"))
        action_count += len(briefing.award_actions)
    cards.append(("ACTIONS", action_count, BLUE))

    gap = 0.015
    width = (0.92 - gap * (len(cards) - 1)) / len(cards)
    height = 0.58 * unit
    for index, (label, value, color) in enumerate(cards):
        x = 0.04 + index * (width + gap)
        axes.add_patch(
            FancyBboxPatch(
                (x, y - height),
                width,
                height,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                facecolor=PANEL,
                edgecolor="none",
            )
        )
        axes.text(
            x + 0.018,
            y - 0.18 * unit,
            str(value),
            color=color,
            fontsize=14,
            fontweight="bold",
            va="center",
        )
        axes.text(
            x + 0.018,
            y - 0.43 * unit,
            label,
            color=MUTED,
            fontsize=7,
            fontweight="bold",
            va="center",
        )
    return y - 0.82 * unit


def _draw_pressure_bar(
    axes,
    *,
    y: float,
    label: str,
    overdue: int,
    due_soon: int,
    current: int,
    on_loa: int,
    unit: float,
) -> float:
    axes.text(
        0.04,
        y,
        label,
        color=TEXT,
        fontsize=10,
        fontweight="bold",
        va="top",
    )
    axes.text(
        0.96,
        y,
        _pressure_summary(
            overdue=overdue,
            due_soon=due_soon,
            on_loa=on_loa,
        ),
        color=MUTED,
        fontsize=9,
        ha="right",
        va="top",
    )
    bar_y = y - 0.32 * unit
    bar_height = 0.13 * unit
    track = FancyBboxPatch(
        (0.04, bar_y),
        0.92,
        bar_height,
        boxstyle=f"round,pad=0,rounding_size={bar_height / 2}",
        facecolor=TRACK,
        edgecolor="none",
    )
    axes.add_patch(track)
    total = overdue + due_soon + current + on_loa
    if total:
        left = 0.04
        for count, color in (
            (overdue, RED),
            (due_soon, AMBER),
            (on_loa, GREY),
            (current, GREEN),
        ):
            width = 0.92 * count / total
            if width:
                segment = Rectangle(
                    (left, bar_y),
                    width,
                    bar_height,
                    facecolor=color,
                    edgecolor="none",
                )
                segment.set_clip_path(track)
                axes.add_patch(segment)
                left += width
    return y - 0.66 * unit


def _draw_attention_row(
    axes,
    row: AttentionRow,
    *,
    avatar_png: bytes | None,
    y: float,
    unit: float,
    figure_height: float,
) -> None:
    row_height = 0.34 * unit
    status_color = RED if row.is_overdue else GREY if row.is_loa_only else AMBER
    status_y = y - row_height / 2
    axes.add_patch(
        FancyBboxPatch(
            (0.04, y - row_height),
            0.92,
            row_height,
            boxstyle="round,pad=0.005,rounding_size=0.012",
            facecolor=PANEL,
            edgecolor="none",
        )
    )
    axes.add_patch(
        Rectangle(
            (0.04, y - row_height + 0.03 * unit),
            0.004,
            row_height - 0.06 * unit,
            facecolor=status_color,
            edgecolor="none",
        )
    )
    if not _draw_avatar(
        axes,
        avatar_png=avatar_png,
        center_y=status_y,
        figure_height=figure_height,
    ):
        _draw_initials_badge(
            axes,
            sailor_id=row.sailor_id,
            sailor_name=row.sailor_name,
            center_y=status_y,
        )
    axes.text(
        0.105,
        status_y,
        row.sailor_name,
        color=TEXT,
        fontsize=9.5,
        va="center",
    )
    right = 0.945
    for requirement in reversed(row.requirements):
        text = f"{requirement.label} · {_chase_age(requirement.entry)}"
        if requirement.is_loa_overdue:
            text += " · LOA"
        width = min(0.22, max(0.105, 0.047 + len(text) * 0.0062))
        color = (
            GREY
            if requirement.is_loa_overdue
            else (RED if requirement.entry.status == ChaseStatus.OVERDUE else AMBER)
        )
        _draw_status_pill(
            axes,
            text=text,
            color=color,
            right=right,
            center_y=status_y,
            width=width,
            unit=unit,
        )
        right -= width + 0.008


def _draw_avatar(
    axes,
    *,
    avatar_png: bytes | None,
    center_y: float,
    figure_height: float,
) -> bool:
    if not avatar_png:
        return False
    try:
        image = plt.imread(io.BytesIO(avatar_png), format="png")
    except Exception:
        return False

    center_x = 0.075
    half_width = 0.0125
    half_height = half_width * 8 / figure_height
    clip = Ellipse(
        (center_x, center_y),
        width=half_width * 2,
        height=half_height * 2,
        transform=axes.transData,
        facecolor="none",
        edgecolor=TEXT,
        linewidth=0.6,
        zorder=4,
    )
    artist = axes.imshow(
        image,
        extent=(
            center_x - half_width,
            center_x + half_width,
            center_y - half_height,
            center_y + half_height,
        ),
        aspect="auto",
        zorder=3,
    )
    artist.set_clip_path(clip)
    axes.add_patch(clip)
    return True


def _draw_initials_badge(
    axes,
    *,
    sailor_id: int,
    sailor_name: str,
    center_y: float,
) -> None:
    axes.scatter(
        [0.075],
        [center_y],
        s=155,
        color=_identity_color(sailor_id),
        edgecolors="none",
        zorder=2,
    )
    axes.text(
        0.075,
        center_y,
        _initials(sailor_name),
        color=TEXT,
        fontsize=6.5,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=3,
    )


def _draw_status_pill(
    axes,
    *,
    text: str,
    color: str,
    right: float,
    center_y: float,
    width: float,
    unit: float,
) -> None:
    height = 0.22 * unit
    axes.add_patch(
        FancyBboxPatch(
            (right - width, center_y - height / 2),
            width,
            height,
            boxstyle=f"round,pad=0.003,rounding_size={height / 2}",
            facecolor=color,
            edgecolor="none",
            alpha=0.12,
        )
    )
    axes.text(
        right - 0.008,
        center_y,
        text,
        color=color,
        fontsize=7.7,
        fontweight="bold",
        ha="right",
        va="center",
    )


def _draw_all_clear(axes, *, y: float, unit: float) -> None:
    height = 0.72 * unit
    axes.add_patch(
        FancyBboxPatch(
            (0.04, y - height),
            0.92,
            height,
            boxstyle="round,pad=0.008,rounding_size=0.015",
            facecolor="#17362a",
            edgecolor=GREEN,
            linewidth=1,
        )
    )
    axes.text(
        0.06,
        y - height / 2,
        "All clear · no requirements are overdue or due soon.",
        color=GREEN,
        fontsize=10,
        fontweight="bold",
        va="center",
    )


def _pack_situation_messages(
    sections: Sequence[tuple[discord.Embed, discord.File | None]],
) -> tuple[BriefingMessage, ...]:
    messages = []
    section_index = 0
    embed_pages = chunk_discord_embeds(tuple(embed for embed, _ in sections))
    for embeds in embed_pages:
        page = sections[section_index : section_index + len(embeds)]
        section_index += len(embeds)
        messages.append(
            BriefingMessage(
                embeds=embeds,
                files=tuple(file for _, file in page if file is not None),
            )
        )
    return tuple(messages)


def _situation_summary(
    briefing: DailyShipBriefing,
    *,
    awards_enabled: bool,
) -> str:
    parts = [
        f"**{briefing.overdue_count} overdue**",
        f"{briefing.due_soon_count} due soon",
    ]
    action_count = len(briefing.requirement_actions)
    if awards_enabled:
        parts.append(f"{len(briefing.pending_awards)} awards pending")
        action_count += len(briefing.award_actions)
    parts.append(f"**{action_count} actions**")
    return " · ".join(parts)


def _tasking_lines(
    actions: tuple[ActionItem, ...],
    *,
    mentions_enabled: bool,
) -> tuple[str, ...]:
    ordered = sorted(
        actions,
        key=lambda action: (
            action.sailor_name.casefold(),
            action.sailor_id,
            action.label.casefold(),
            action.detail.casefold(),
        ),
    )
    lines = []
    for _, sailor_actions in groupby(
        ordered,
        key=lambda action: action.sailor_id,
    ):
        grouped = tuple(sailor_actions)
        requirements = [
            f"{action.label} · {action.detail}"
            for action in grouped
            if action.label != "Award"
        ]
        award_count = sum(action.label == "Award" for action in grouped)
        details = requirements
        if award_count:
            details.append(f"{award_count} award{'s' if award_count != 1 else ''}")
        target = (
            f"<@{grouped[0].sailor_id}>"
            if mentions_enabled
            else f"@<{grouped[0].sailor_id}>"
        )
        recipient = f"{target} · **{grouped[0].sailor_name}**"
        lines.append(f"• {recipient} — {'; '.join(details)}")
    return tuple(lines)


def _task_owner_name(
    actions: Sequence[ActionItem],
    officer_id: int,
) -> str:
    return next(
        (action.responsible_name for action in actions if action.responsible_name),
        f"Officer {officer_id}",
    )


def _chunk_tasking_lines(
    lines: tuple[str, ...],
    *,
    max_length: int,
) -> tuple[str, ...]:
    chunks = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = line
    if current:
        chunks.append(current)
    return tuple(chunks)


def render_pending_award_embeds(
    pending_awards: Sequence[PendingShipAward],
    *,
    subject_name: str,
) -> tuple[discord.Embed, ...]:
    if not pending_awards:
        return (
            discord.Embed(
                title=f"Awards · {subject_name}",
                description="No pending awards.",
                color=discord.Color.green(),
            ),
        )

    awards = sorted(
        pending_awards,
        key=lambda award: (award.sailor_name.casefold(), award.award_name.casefold()),
    )
    pages = [
        awards[index : index + MAX_AWARDS_PER_EMBED]
        for index in range(0, len(awards), MAX_AWARDS_PER_EMBED)
    ]
    embeds = []
    for page, page_awards in enumerate(pages, start=1):
        title = f"Pending awards · {subject_name}"
        if len(pages) > 1:
            title += f" · {page}/{len(pages)}"
        first_award = (page - 1) * MAX_AWARDS_PER_EMBED + 1
        last_award = first_award + len(page_awards) - 1
        embed = discord.Embed(
            title=title,
            description=(
                f"Showing awards **{first_award}–{last_award}** of **{len(awards)}**."
            ),
            color=discord.Color.red(),
        )
        for award in page_awards:
            embed.add_field(
                name=award.sailor_name,
                value=(
                    f"[**{award.award_name}**]({award.details_url})\n"
                    f"**Ranks responsible:** `{award.ranks_responsible}`\n"
                    f"**Responsible CO:** {_award_responsible(award)}"
                ),
                inline=False,
            )
        embeds.append(embed)
    return tuple(embeds)


def _award_responsible(award: PendingShipAward) -> str:
    if award.responsible_id is not None:
        return f"<@{award.responsible_id}>"
    return award.responsible_name or "Unassigned"


def _enabled_actions(
    briefing: DailyShipBriefing,
    *,
    requirements_enabled: bool,
    awards_enabled: bool,
) -> tuple[ActionItem, ...]:
    return (
        *(briefing.requirement_actions if requirements_enabled else ()),
        *(briefing.award_actions if awards_enabled else ()),
    )


def _member_baseline(
    member,
    role_added_at: datetime | None,
    reference_time: datetime,
) -> datetime:
    candidate = role_added_at or getattr(member, "joined_at", None) or reference_time
    return _ensure_utc(candidate)


def _member_is_on_loa(member) -> bool:
    return (
        re.match(
            r"^\[LOA(?:-\d+)?\]",
            member.display_name,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _acting_officer_id(member, guild) -> int | None:
    try:
        officer = SailorCO(member, guild).acting
    except (AttributeError, IndexError, RecursionError, TypeError):
        return None
    return officer.id if officer is not None else None


def _responsible_name(guild, responsible_id: int | None) -> str | None:
    if responsible_id is None:
        return None
    get_member = getattr(guild, "get_member", None)
    if not callable(get_member):
        return None
    member = get_member(responsible_id)
    return member.display_name if member is not None else None


def _count_status(
    entries: list[ChaseEntry],
    status: ChaseStatus,
) -> int:
    return sum(entry.status == status for entry in entries)


def _chase_sort_key(entry: ChaseEntry) -> tuple[int, int, str]:
    status_order = 0 if entry.status == ChaseStatus.OVERDUE else 1
    days = -entry.days if entry.status == ChaseStatus.OVERDUE else entry.days
    return status_order, days, entry.sailor_name.casefold()


def _attention_sort_key(row: AttentionRow) -> tuple[int, int, str]:
    overdue_days = [
        requirement.entry.days
        for requirement in row.requirements
        if (
            requirement.entry.status == ChaseStatus.OVERDUE
            and not requirement.is_loa_overdue
        )
    ]
    if overdue_days:
        return 0, -max(overdue_days), row.sailor_name.casefold()
    loa_days = [
        requirement.entry.days
        for requirement in row.requirements
        if requirement.is_loa_overdue
    ]
    if loa_days:
        return 1, -max(loa_days), row.sailor_name.casefold()
    days_left = [requirement.entry.days for requirement in row.requirements]
    return 2, min(days_left), row.sailor_name.casefold()


def _attention_section(row: AttentionRow) -> str:
    if row.is_overdue:
        return "REQUIRES ACTION"
    if row.is_loa_only:
        return "ON LEAVE"
    return "COMING DUE"


def _chase_age(entry: ChaseEntry) -> str:
    if entry.missing_history:
        return f"{entry.days}d no activity"
    if entry.status == ChaseStatus.OVERDUE:
        return f"{entry.days}d late"
    return f"{entry.days}d left"


def _initials(name: str) -> str:
    cleaned_name = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", name).strip()
    words = re.findall(r"[A-Za-z0-9]+", cleaned_name)
    if not words:
        return "?"
    return "".join(word[0].upper() for word in words[:2])


def _pressure_summary(
    *,
    overdue: int,
    due_soon: int,
    on_loa: int = 0,
) -> str:
    parts = []
    if overdue:
        parts.append(f"{overdue} overdue")
    if due_soon:
        parts.append(f"{due_soon} due soon")
    if on_loa:
        parts.append(f"{on_loa} on LOA")
    return " · ".join(parts) if parts else "All current"


def _identity_color(sailor_id: int) -> str:
    palette = (BLUE, GREEN, "#b06cff", "#f06ec7", "#ef7d32", "#25b8c7")
    return palette[sailor_id % len(palette)]


def _daily_color(
    briefing: DailyShipBriefing,
    *,
    include_awards: bool,
) -> discord.Color:
    if briefing.requirement_actions or (include_awards and briefing.award_actions):
        return discord.Color.red()
    return discord.Color.green()


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
