from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import discord

from src.data.repository.auditlog_repository import AuditLogRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.data.structs import NavyRank
from src.utils.time_utils import utc_time_now


class RequirementStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class RequirementSpec:
    type: str
    label: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PromotionPathSpec:
    next_rank_index: int
    required_requirements: tuple[RequirementSpec, ...] = ()
    additional_requirements: tuple[RequirementSpec, ...] = ()
    flavor_requirements: tuple[RequirementSpec, ...] = ()
    use_rank_additional_fallback: bool = True
    show_or_separator_after: bool = False


@dataclass(slots=True)
class PromotionContext:
    guild_member: discord.Member
    guild_member_role_ids: set[int]
    netc_guild_member_role_ids: set[int]
    target_id: int
    voyage_count: int
    hosted_count: int
    current_rank: NavyRank
    is_marine: bool
    audit_log_repository: AuditLogRepository
    voyage_repository: VoyageRepository
    now: datetime = field(default_factory=utc_time_now)


@dataclass(frozen=True, slots=True)
class EvaluatedRequirement:
    status: RequirementStatus
    lines: tuple[str, ...]
    summary: str = ""


@dataclass(frozen=True, slots=True)
class PromotionEvaluation:
    next_rank: NavyRank
    next_rank_display_name: str
    required_requirements: tuple[EvaluatedRequirement, ...]
    additional_requirements: tuple[EvaluatedRequirement, ...]
    flavor_requirements: tuple[EvaluatedRequirement, ...]
    show_or_separator_after: bool = False


@dataclass(frozen=True, slots=True)
class RenderedField:
    name: str
    value: str
    inline: bool = False


@dataclass(frozen=True, slots=True)
class RenderedPromotionSections:
    fields: tuple[RenderedField, ...]
    has_required_failures: bool = False
    has_required_information: bool = False
    has_required_successes: bool = False
    show_or_separator_after: bool = False
