from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, date, datetime, time

from discord.utils import escape_markdown, escape_mentions

from src.data.models import Sailor
from src.notifications.date_utils import ensure_utc
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    NotificationField,
    NotificationPayload,
    ResolvedMemberContext,
    TemplateKey,
)
from src.utils.emoji_utils import resolve_ship_emoji
from src.utils.ship_utils import get_ship_by_role_id


class NotificationPayloadFactory:
    def build(
            self,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            eligibility: EligibilityResult,
            reference_time: datetime | None = None,
    ) -> NotificationPayload:
        subject_name = self._sanitize_subject_name(
            member_context.display_name or sailor.gamertag or str(sailor.discord_id)
        )
        ship = (
            get_ship_by_role_id(member_context.ship_role_id)
            if member_context.ship_role_id
            else None
        )
        resolved_reference_time = ensure_utc(reference_time or datetime.now(UTC))
        ship_emoji = resolve_ship_emoji(ship_role_id=member_context.ship_role_id, ship=ship)
        status_label = self._build_status_label(eligibility.days_remaining)
        due_timestamp = self._format_relative_datetime(eligibility.threshold_at)

        if definition.template_key == TemplateKey.NO_VOYAGE_REMINDER:
            title = f"{ship_emoji} Voyaging inactivity reminder"
            body = self._build_body(
                subject_name,
                sailor.discord_id,
                due_timestamp,
                f"{definition.threshold_days} days without voyaging",
                is_overdue=eligibility.threshold_at <= resolved_reference_time,
            )
            activity_label = "Last Voyage"
        else:
            title = f"{ship_emoji} Hosting inactivity reminder"
            body = self._build_body(
                subject_name,
                sailor.discord_id,
                due_timestamp,
                f"{definition.threshold_days} days without hosting",
                is_overdue=eligibility.threshold_at <= resolved_reference_time,
            )
            activity_label = "Last Hosting"

        return NotificationPayload(
            notification_type=definition.notification_type.value,
            template_key=definition.template_key.value,
            title=title,
            body=body,
            severity="warning",
            subject_name=subject_name,
            ship_name=member_context.ship_name,
            source_activity_label=activity_label,
            source_activity_date=self._format_datetime(eligibility.source_activity_at),
            threshold_date=self._format_date(eligibility.threshold_date),
            days_remaining_label=status_label,
            footer=f"{definition.notification_type.value}",
            thumbnail_url=member_context.avatar_url,
            display_fields=(),
            metadata={
                "ship_role_id": str(member_context.ship_role_id or ""),
                "squad_role_id": str(member_context.squad_role_id or ""),
                "threshold_at": eligibility.threshold_at.isoformat(),
                "scheduled_for_at": eligibility.scheduled_for_at.isoformat(),
                "scheduled_for_date": eligibility.scheduled_for_date.isoformat(),
                "ship_emoji": ship_emoji,
            },
        )

    @staticmethod
    def to_snapshot(payload: NotificationPayload) -> str:
        data = asdict(payload)
        data["display_fields"] = [asdict(field) for field in payload.display_fields]
        return json.dumps(data, sort_keys=True)

    @staticmethod
    def from_snapshot(payload_snapshot: str) -> NotificationPayload:
        data = json.loads(payload_snapshot)
        display_fields = tuple(NotificationField(**field) for field in data["display_fields"])
        return NotificationPayload(**{**data, "display_fields": display_fields})

    @staticmethod
    def _build_body(
            subject_name: str,
            sailor_id: int,
            due_timestamp: str,
            threshold_label: str,
            is_overdue: bool,
    ) -> str:
        """
        Build a clearer body message for a notification.

        - Avoid repeating the user's display name directly after the mention (that produced
          messages like: "@Name Name is due ..."). We keep the mention only.
        - Use "to reach" for upcoming due dates for readability, keep "for reaching" when overdue.
        """
        status_phrase = "became due" if is_overdue else "is due"
        if is_overdue:
            # Overdue: keep phrasing that indicates it already became due
            return f"<@{sailor_id}> {status_phrase} {due_timestamp} for reaching {threshold_label}."
        # Upcoming: use 'to reach' and omit the redundant display name after the mention
        return f"<@{sailor_id}> {status_phrase} {due_timestamp} to reach {threshold_label}."

    @staticmethod
    def _build_status_label(days_remaining: int) -> str:
        if days_remaining == 0:
            return "Due today"
        if days_remaining < 0:
            return f"{abs(days_remaining)} day(s) overdue"
        return f"{days_remaining} day(s) remaining"

    @staticmethod
    def _sanitize_subject_name(value: str) -> str:
        return escape_mentions(escape_markdown(value))

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        timestamp = int(value.astimezone(UTC).timestamp())
        return f"<t:{timestamp}:f> (<t:{timestamp}:R>)"

    @staticmethod
    def _format_date(value: date) -> str:
        timestamp = int(datetime.combine(value, time.min, tzinfo=UTC).timestamp())
        return f"<t:{timestamp}:D>"

    @staticmethod
    def _format_relative_datetime(value: datetime) -> str:
        timestamp = int(value.astimezone(UTC).timestamp())
        return f"<t:{timestamp}:R>"
