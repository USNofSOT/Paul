from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class NotificationType(StrEnum):
    NO_VOYAGE_REMINDER = "NO_VOYAGE_REMINDER"
    NO_HOSTING_REMINDER = "NO_HOSTING_REMINDER"


class RoutingTargetType(StrEnum):
    SHIP_COMMAND_CHANNEL = "SHIP_COMMAND_CHANNEL"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"


class TemplateKey(StrEnum):
    NO_VOYAGE_REMINDER = "NO_VOYAGE_REMINDER"
    NO_HOSTING_REMINDER = "NO_HOSTING_REMINDER"


@dataclass(frozen=True)
class NotificationDefinition:
    notification_type: NotificationType
    activity_field: str
    threshold_days: int
    trigger_offsets: tuple[int, ...]
    template_key: TemplateKey
    routing_target: RoutingTargetType


@dataclass(frozen=True)
class ResolvedMemberContext:
    sailor_id: int
    display_name: str
    ship_role_id: int | None
    ship_name: str | None
    squad_role_id: int | None
    squad_name: str | None
    avatar_url: str | None = None


@dataclass(frozen=True)
class EligibilityResult:
    source_activity_at: datetime
    source_activity_date: date
    threshold_at: datetime
    threshold_date: date
    trigger_offset: int
    scheduled_for_date: date
    days_remaining: int


@dataclass(frozen=True)
class NotificationField:
    name: str
    value: str
    inline: bool = False


@dataclass(frozen=True)
class NotificationPayload:
    notification_type: str
    template_key: str
    title: str
    body: str
    severity: str
    subject_name: str
    ship_name: str | None
    source_activity_label: str
    source_activity_date: str
    threshold_date: str
    days_remaining_label: str
    footer: str
    thumbnail_url: str | None = None
    display_fields: tuple[NotificationField, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolvedRoute:
    destination_channel_id: int | None
    skip_reason: str | None = None


@dataclass(frozen=True)
class RenderedNotification:
    embed_title: str
    embed_description: str
    fields: tuple[NotificationField, ...]
    footer: str
    color_value: int
    thumbnail_url: str | None = None
