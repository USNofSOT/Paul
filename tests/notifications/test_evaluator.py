import unittest
from datetime import UTC, datetime, timedelta

from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.data.models import NotificationEvent, Sailor
from src.notifications.evaluator import SailorInactivityEligibilityEvaluator
from src.notifications.types import (
    NotificationDefinition,
    NotificationType,
    ResolvedMemberContext,
    RoutingTargetType,
    TemplateKey,
)


class TestSailorInactivityEligibilityEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = SailorInactivityEligibilityEvaluator()
        self.member_context = ResolvedMemberContext(
            sailor_id=1,
            display_name="Sailor One",
            ship_role_id=123,
            ship_name="USS Test",
            squad_role_id=None,
            squad_name=None,
        )

    def test_voyage_projection_uses_exact_threshold_and_sparse_offsets(self) -> None:
        sailor = Sailor(
            discord_id=1,
            last_voyage_at=datetime(2026, 3, 1, 23, 30, tzinfo=UTC),
        )
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_VOYAGE_REMINDER,
            activity_field="last_voyage_at",
            threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-7, -3, 0, 7),
            template_key=TemplateKey.NO_VOYAGE_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        projected = self.evaluator.project_for_window(
            definition,
            sailor,
            self.member_context,
            datetime(2026, 3, 22, 0, 0, tzinfo=UTC),
            datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
        )

        self.assertEqual([result.trigger_offset for result in projected], [-7, -3, 0, 7])
        self.assertEqual(
            [result.scheduled_for_at.isoformat() for result in projected],
            [
                "2026-03-22T23:30:00+00:00",
                "2026-03-26T23:30:00+00:00",
                "2026-03-29T23:30:00+00:00",
                "2026-04-05T23:30:00+00:00",
            ],
        )
        self.assertEqual(projected[-1].threshold_at.isoformat(), "2026-03-29T23:30:00+00:00")
        self.assertEqual(projected[-1].days_remaining, -7)

    def test_hosting_projection_excludes_events_outside_lookahead(self) -> None:
        sailor = Sailor(
            discord_id=4,
            last_hosting_at=datetime(2026, 3, 20, 12, 0, tzinfo=UTC),
        )
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, 0, 7),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        projected = self.evaluator.project_for_window(
            definition,
            sailor,
            self.member_context,
            datetime(2026, 3, 31, 0, 0, tzinfo=UTC),
            datetime(2026, 4, 1, 23, 59, tzinfo=UTC),
        )

        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0].trigger_offset, -3)
        self.assertEqual(projected[0].scheduled_for_at.isoformat(), "2026-03-31T12:00:00+00:00")

    def test_null_baseline_is_excluded(self) -> None:
        sailor = Sailor(discord_id=2, last_hosting_at=None)
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, 0, 7),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        projected = self.evaluator.project_for_window(
            definition,
            sailor,
            self.member_context,
            datetime(2026, 4, 1, 0, 0, tzinfo=UTC),
            datetime(2026, 4, 2, 0, 0, tzinfo=UTC),
        )

        self.assertEqual(projected, ())

    def test_matches_event_false_when_activity_cycle_changes(self) -> None:
        sailor = Sailor(
            discord_id=3,
            last_voyage_at=datetime(2026, 3, 5, 12, 0, tzinfo=UTC),
        )
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_VOYAGE_REMINDER,
            activity_field="last_voyage_at",
            threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-7, -3, 0, 7),
            template_key=TemplateKey.NO_VOYAGE_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )
        event = NotificationEvent(
            id=99,
            notification_type=definition.notification_type.value,
            status="pending",
            sailor_id=3,
            ship_role_id=123,
            squad_role_id=None,
            source_activity_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            source_activity_date=datetime(2026, 3, 1, 12, 0, tzinfo=UTC).date(),
            threshold_at=datetime(2026, 3, 29, 12, 0, tzinfo=UTC),
            threshold_date=datetime(2026, 3, 29, 12, 0, tzinfo=UTC).date(),
            trigger_offset=-7,
            scheduled_for_at=datetime(2026, 3, 22, 12, 0, tzinfo=UTC),
            scheduled_for_date=datetime(2026, 3, 22, 12, 0, tzinfo=UTC).date(),
            destination_channel_id=1,
            payload_snapshot="{}",
            created_at=datetime(2026, 3, 21, 0, 0, tzinfo=UTC),
            updated_at=datetime(2026, 3, 21, 0, 0, tzinfo=UTC),
        )

        self.assertFalse(
            self.evaluator.matches_event(definition, sailor, self.member_context, event)
        )

    def test_matches_event_true_for_current_cycle(self) -> None:
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, 0, 7),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )
        sailor = Sailor(
            discord_id=5,
            last_hosting_at=datetime(2026, 3, 20, 12, 0, tzinfo=UTC),
        )
        threshold_at = sailor.last_hosting_at + timedelta(days=HOSTING_REQUIREMENT_IN_DAYS)
        scheduled_for_at = threshold_at + timedelta(days=-3)
        event = NotificationEvent(
            id=5,
            notification_type=definition.notification_type.value,
            status="pending",
            sailor_id=5,
            ship_role_id=123,
            squad_role_id=None,
            source_activity_at=sailor.last_hosting_at,
            source_activity_date=sailor.last_hosting_at.date(),
            threshold_at=threshold_at,
            threshold_date=threshold_at.date(),
            trigger_offset=-3,
            scheduled_for_at=scheduled_for_at,
            scheduled_for_date=scheduled_for_at.date(),
            destination_channel_id=1,
            payload_snapshot="{}",
            created_at=datetime(2026, 3, 30, 0, 0, tzinfo=UTC),
            updated_at=datetime(2026, 3, 30, 0, 0, tzinfo=UTC),
        )

        self.assertTrue(
            self.evaluator.matches_event(definition, sailor, self.member_context, event)
        )
