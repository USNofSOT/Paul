from __future__ import annotations

from datetime import date, timedelta

from src.data.models import Sailor
from src.notifications.date_utils import ensure_utc, to_local_date
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    ResolvedMemberContext,
)


class SailorInactivityEligibilityEvaluator:
    def evaluate(
            self,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            evaluation_date: date,
    ) -> EligibilityResult | None:
        del member_context

        source_activity_at = getattr(sailor, definition.activity_field)
        if source_activity_at is None:
            return None

        normalized_source_activity_at = ensure_utc(source_activity_at)
        source_activity_date = to_local_date(normalized_source_activity_at)
        threshold_at = normalized_source_activity_at + timedelta(days=definition.threshold_days)
        threshold_date = threshold_at.date()
        trigger_offset = (evaluation_date - threshold_date).days
        if trigger_offset not in definition.trigger_offsets:
            return None

        return EligibilityResult(
            source_activity_at=normalized_source_activity_at,
            source_activity_date=source_activity_date,
            threshold_at=threshold_at,
            threshold_date=threshold_date,
            trigger_offset=trigger_offset,
            scheduled_for_date=evaluation_date,
            days_remaining=max((threshold_date - evaluation_date).days, 0),
        )
