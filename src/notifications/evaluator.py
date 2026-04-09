from __future__ import annotations

from datetime import datetime, timedelta

from src.data.models import NotificationEvent, Sailor
from src.notifications.date_utils import ensure_utc, to_local_date
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    ResolvedMemberContext,
)


class SailorInactivityEligibilityEvaluator:
    def project_for_window(
            self,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            window_start: datetime,
            window_end: datetime,
    ) -> tuple[EligibilityResult, ...]:
        del member_context

        source_activity_at = getattr(sailor, definition.activity_field)
        if source_activity_at is None:
            return ()

        normalized_source_activity_at = ensure_utc(source_activity_at)
        resolved_window_start = ensure_utc(window_start)
        resolved_window_end = ensure_utc(window_end)
        source_activity_date = to_local_date(normalized_source_activity_at)
        threshold_at = normalized_source_activity_at + timedelta(days=definition.threshold_days)
        threshold_date = threshold_at.date()

        projected_results: list[EligibilityResult] = []
        for trigger_offset in definition.trigger_offsets:
            scheduled_for_at = threshold_at + timedelta(days=trigger_offset)
            if scheduled_for_at < resolved_window_start or scheduled_for_at > resolved_window_end:
                continue

            scheduled_for_date = scheduled_for_at.date()
            projected_results.append(
                EligibilityResult(
                    source_activity_at=normalized_source_activity_at,
                    source_activity_date=source_activity_date,
                    threshold_at=threshold_at,
                    threshold_date=threshold_date,
                    trigger_offset=trigger_offset,
                    scheduled_for_at=scheduled_for_at,
                    scheduled_for_date=scheduled_for_date,
                    days_remaining=(threshold_date - scheduled_for_date).days,
                )
            )

        return tuple(projected_results)

    def matches_event(
            self,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            event: NotificationEvent,
    ) -> bool:
        del member_context

        source_activity_at = getattr(sailor, definition.activity_field)
        if source_activity_at is None:
            return False

        normalized_source_activity_at = ensure_utc(source_activity_at)
        threshold_at = normalized_source_activity_at + timedelta(days=definition.threshold_days)
        scheduled_for_at = threshold_at + timedelta(days=event.trigger_offset)

        return (
                normalized_source_activity_at == ensure_utc(event.source_activity_at)
                and to_local_date(normalized_source_activity_at) == event.source_activity_date
                and threshold_at == ensure_utc(event.threshold_at)
                and threshold_at.date() == event.threshold_date
                and scheduled_for_at == ensure_utc(event.scheduled_for_at)
                and scheduled_for_at.date() == event.scheduled_for_date
        )
