import unittest
from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.requirements import VOYAGING_REQUIREMENT_IN_DAYS
from src.data.models import NotificationEvent, Sailor
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    NotificationStatus,
    NotificationType,
    RoutingTargetType,
    TemplateKey,
    ResolvedMemberContext,
)


class TestNotificationEventRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Sailor.__table__.create(self.engine)
        NotificationEvent.__table__.create(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.repository = NotificationEventRepository()
        self.repository.session = self.session

        self.sailor = Sailor(discord_id=1, gamertag="Repo Sailor")
        self.session.add(self.sailor)
        self.session.commit()

        self.definition = NotificationDefinition(
            notification_type=NotificationType.NO_VOYAGE_REMINDER,
            activity_field="last_voyage_at",
            threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-7, -6, -5, -4, -3, -2, -1, 0),
            template_key=TemplateKey.NO_VOYAGE_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )
        self.member_context = ResolvedMemberContext(
            sailor_id=1,
            display_name="Repo Sailor",
            ship_role_id=10,
            ship_name="USS Test",
            squad_role_id=20,
            squad_name="Alpha Squad",
        )
        self.eligibility = EligibilityResult(
            source_activity_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            source_activity_date=date(2026, 3, 1),
            threshold_at=datetime(2026, 3, 29, 12, 0, tzinfo=UTC),
            threshold_date=date(2026, 3, 29),
            trigger_offset=-7,
            scheduled_for_at=datetime(2026, 3, 22, 12, 0, tzinfo=UTC),
            scheduled_for_date=date(2026, 3, 22),
            days_remaining=7,
        )

    def tearDown(self) -> None:
        self.session.close()
        NotificationEvent.__table__.drop(self.engine)
        Sailor.__table__.drop(self.engine)

    def test_create_pending_event_deduplicates_by_exact_cycle(self) -> None:
        first, created_first = self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=self.eligibility,
            destination_channel_id=999,
            payload_snapshot="{}",
        )
        second, created_second = self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=self.eligibility,
            destination_channel_id=999,
            payload_snapshot="{}",
        )

        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.session.query(NotificationEvent).count(), 1)

    def test_list_due_event_ids_uses_exact_schedule_order(self) -> None:
        first_eligibility = self.eligibility
        second_eligibility = EligibilityResult(
            source_activity_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            source_activity_date=date(2026, 3, 1),
            threshold_at=datetime(2026, 3, 29, 12, 0, tzinfo=UTC),
            threshold_date=date(2026, 3, 29),
            trigger_offset=-3,
            scheduled_for_at=datetime(2026, 3, 26, 12, 0, tzinfo=UTC),
            scheduled_for_date=date(2026, 3, 26),
            days_remaining=3,
        )
        self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=second_eligibility,
            destination_channel_id=999,
            payload_snapshot="{}",
        )
        self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=first_eligibility,
            destination_channel_id=999,
            payload_snapshot="{}",
        )

        due_event_ids = self.repository.list_due_event_ids(
            limit=10,
            due_before=datetime(2026, 3, 23, 0, 0, tzinfo=UTC),
        )

        self.assertEqual(len(due_event_ids), 1)
        self.assertEqual(
            self.repository.get_event(due_event_ids[0]).scheduled_for_at.isoformat(),
            "2026-03-22T12:00:00",
        )

    def test_claim_and_retry_state_transitions(self) -> None:
        event, _ = self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=self.eligibility,
            destination_channel_id=999,
            payload_snapshot="{}",
        )

        claimed = self.repository.claim_event(event.id)
        self.assertTrue(claimed)
        self.assertEqual(
            self.repository.get_event(event.id).status,
            NotificationStatus.PROCESSING.value,
        )

        attempt_count = self.repository.release_for_retry(event.id, "temporary failure")
        self.assertEqual(attempt_count, 1)
        retried_event = self.repository.get_event(event.id)
        self.assertEqual(retried_event.status, NotificationStatus.PENDING.value)
        self.assertEqual(retried_event.attempt_count, 1)

        final_attempt = self.repository.mark_failed(event.id, "permanent failure")
        self.assertEqual(final_attempt, 2)
        failed_event = self.repository.get_event(event.id)
        self.assertEqual(failed_event.status, NotificationStatus.FAILED.value)
        self.assertEqual(failed_event.failure_reason, "permanent failure")

    def test_update_payload_snapshot_refreshes_processing_event(self) -> None:
        event, _ = self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=self.eligibility,
            destination_channel_id=999,
            payload_snapshot='{"body":"before"}',
        )

        self.assertTrue(self.repository.claim_event(event.id))
        self.repository.update_payload_snapshot(event.id, '{"body":"after"}')

        refreshed_event = self.repository.get_event(event.id)
        self.assertEqual(refreshed_event.status, NotificationStatus.PROCESSING.value)
        self.assertEqual(refreshed_event.payload_snapshot, '{"body":"after"}')

    def test_recent_events_and_status_counts(self) -> None:
        first_event, _ = self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=self.eligibility,
            destination_channel_id=999,
            payload_snapshot='{"body":"first"}',
        )
        self.repository.mark_delivered(first_event.id)

        second_eligibility = EligibilityResult(
            source_activity_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            source_activity_date=date(2026, 3, 1),
            threshold_at=datetime(2026, 3, 29, 12, 0, tzinfo=UTC),
            threshold_date=date(2026, 3, 29),
            trigger_offset=-6,
            scheduled_for_at=datetime(2026, 3, 23, 12, 0, tzinfo=UTC),
            scheduled_for_date=date(2026, 3, 23),
            days_remaining=6,
        )
        second_event, _ = self.repository.create_pending_event(
            definition=self.definition,
            sailor=self.sailor,
            member_context=self.member_context,
            eligibility=second_eligibility,
            destination_channel_id=999,
            payload_snapshot='{"body":"second"}',
        )
        self.repository.mark_skipped(second_event.id, "testing")

        recent_events = self.repository.list_recent_events(limit=2)
        status_counts = self.repository.count_by_status()

        self.assertEqual(len(recent_events), 2)
        self.assertEqual(recent_events[0].id, second_event.id)
        self.assertEqual(status_counts[NotificationStatus.DELIVERED.value], 1)
        self.assertEqual(status_counts[NotificationStatus.SKIPPED.value], 1)
