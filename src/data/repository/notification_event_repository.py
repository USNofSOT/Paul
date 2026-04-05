from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from src.data.models import NotificationEvent, Sailor
from src.data.repository.common.base_repository import BaseRepository
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    NotificationStatus,
    ResolvedMemberContext,
)

log = logging.getLogger(__name__)


class NotificationEventRepository(BaseRepository[NotificationEvent]):
    def __init__(self) -> None:
        super().__init__(NotificationEvent)

    def create_pending_event(
            self,
            *,
            definition: NotificationDefinition,
            sailor: Sailor,
            member_context: ResolvedMemberContext,
            eligibility: EligibilityResult,
            destination_channel_id: int | None,
            payload_snapshot: str,
    ) -> tuple[NotificationEvent, bool]:
        now = datetime.now(UTC)
        event = NotificationEvent(
            notification_type=definition.notification_type.value,
            status=NotificationStatus.PENDING.value,
            sailor_id=sailor.discord_id,
            ship_role_id=member_context.ship_role_id,
            squad_role_id=member_context.squad_role_id,
            source_activity_at=eligibility.source_activity_at,
            source_activity_date=eligibility.source_activity_date,
            threshold_date=eligibility.threshold_date,
            trigger_offset=eligibility.trigger_offset,
            scheduled_for_date=eligibility.scheduled_for_date,
            destination_channel_id=destination_channel_id,
            payload_snapshot=payload_snapshot,
            created_at=now,
            updated_at=now,
        )
        try:
            self.session.add(event)
            self.session.commit()
            return event, True
        except IntegrityError:
            self.session.rollback()
            existing = (
                self.session.query(NotificationEvent)
                .filter(
                    NotificationEvent.notification_type == definition.notification_type.value,
                    NotificationEvent.sailor_id == sailor.discord_id,
                    NotificationEvent.threshold_date == eligibility.threshold_date,
                    NotificationEvent.trigger_offset == eligibility.trigger_offset,
                )
                .first()
            )
            return existing, False

    def list_pending_event_ids(self, *, limit: int) -> list[int]:
        rows = (
            self.session.query(NotificationEvent.id)
            .filter(NotificationEvent.status == NotificationStatus.PENDING.value)
            .order_by(NotificationEvent.scheduled_for_date.asc(), NotificationEvent.id.asc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]

    def claim_event(self, event_id: int) -> bool:
        updated = (
            self.session.query(NotificationEvent)
            .filter(
                NotificationEvent.id == event_id,
                NotificationEvent.status == NotificationStatus.PENDING.value,
            )
            .update(
                {
                    NotificationEvent.status: NotificationStatus.PROCESSING.value,
                    NotificationEvent.claimed_at: datetime.now(UTC),
                    NotificationEvent.updated_at: datetime.now(UTC),
                },
                synchronize_session=False,
            )
        )
        self.session.commit()
        return updated == 1

    def get_event(self, event_id: int) -> NotificationEvent | None:
        return (
            self.session.query(NotificationEvent)
            .filter(NotificationEvent.id == event_id)
            .first()
        )

    def list_recent_events(self, *, limit: int = 10) -> list[NotificationEvent]:
        return (
            self.session.query(NotificationEvent)
            .order_by(NotificationEvent.created_at.desc(), NotificationEvent.id.desc())
            .limit(limit)
            .all()
        )

    def count_by_status(self) -> dict[str, int]:
        rows = (
            self.session.query(
                NotificationEvent.status,
                func.count(NotificationEvent.id),
            )
            .group_by(NotificationEvent.status)
            .all()
        )
        counts = {status: count for status, count in rows}
        return {
            status.value: counts.get(status.value, 0)
            for status in NotificationStatus
        }

    def update_payload_snapshot(self, event_id: int, payload_snapshot: str) -> None:
        self._update_status(
            event_id=event_id,
            status=NotificationStatus.PROCESSING.value,
            payload_snapshot=payload_snapshot,
        )

    def mark_delivered(self, event_id: int) -> None:
        self._update_status(
            event_id=event_id,
            status=NotificationStatus.DELIVERED.value,
            delivered_at=datetime.now(UTC),
            failure_reason=None,
            skip_reason=None,
        )

    def mark_skipped(self, event_id: int, reason: str) -> None:
        self._update_status(
            event_id=event_id,
            status=NotificationStatus.SKIPPED.value,
            skip_reason=reason,
        )

    def release_for_retry(self, event_id: int, reason: str) -> int:
        event = self.get_event(event_id)
        if event is None:
            return 0

        next_attempt = int(event.attempt_count or 0) + 1
        self._update_status(
            event_id=event_id,
            status=NotificationStatus.PENDING.value,
            attempt_count=next_attempt,
            failure_reason=reason,
            claimed_at=None,
        )
        return next_attempt

    def mark_failed(self, event_id: int, reason: str) -> int:
        event = self.get_event(event_id)
        if event is None:
            return 0

        final_attempt = int(event.attempt_count or 0) + 1
        self._update_status(
            event_id=event_id,
            status=NotificationStatus.FAILED.value,
            attempt_count=final_attempt,
            failure_reason=reason,
        )
        return final_attempt

    def _update_status(self, event_id: int, status: str, **extra_fields) -> None:
        fields = {
            NotificationEvent.status: status,
            NotificationEvent.updated_at: datetime.now(UTC),
            **{
                getattr(NotificationEvent, key): value
                for key, value in extra_fields.items()
            },
        }
        (
            self.session.query(NotificationEvent)
            .filter(NotificationEvent.id == event_id)
            .update(fields, synchronize_session=False)
        )
        self.session.commit()
