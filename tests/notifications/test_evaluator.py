import unittest
from datetime import UTC, date, datetime

from src.config.requirements import (
    HOSTING_REQUIREMENT_IN_DAYS,
    VOYAGING_REQUIREMENT_IN_DAYS,
)
from src.data.models import Sailor
from src.notifications.evaluator import SailorInactivityEligibilityEvaluator
from src.notifications.types import (
    NotificationDefinition,
    NotificationType,
    RoutingTargetType,
    TemplateKey,
    ResolvedMemberContext,
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

    def test_voyage_trigger_window_uses_utc_date(self) -> None:
        sailor = Sailor(
            discord_id=1,
            last_voyage_at=datetime(2026, 3, 1, 23, 30, tzinfo=UTC),
        )
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_VOYAGE_REMINDER,
            activity_field="last_voyage_at",
            threshold_days=VOYAGING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-7, -6, -5, -4, -3, -2, -1, 0),
            template_key=TemplateKey.NO_VOYAGE_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        expected_threshold_date = date(2026, 3, 29)
        for trigger_offset in definition.trigger_offsets:
            evaluation_date = date.fromordinal(
                expected_threshold_date.toordinal() + trigger_offset
            )
            with self.subTest(trigger_offset=trigger_offset):
                result = self.evaluator.evaluate(
                    definition,
                    sailor,
                    self.member_context,
                    evaluation_date,
                )

                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result.source_activity_date.isoformat(), "2026-03-01")
                self.assertEqual(result.threshold_at.isoformat(), "2026-03-29T23:30:00+00:00")
                self.assertEqual(result.threshold_date, expected_threshold_date)
                self.assertEqual(result.trigger_offset, trigger_offset)
                self.assertEqual(
                    result.days_remaining,
                    max((expected_threshold_date - evaluation_date).days, 0),
                )

    def test_hosting_trigger_window_uses_all_daily_offsets(self) -> None:
        sailor = Sailor(
            discord_id=4,
            last_hosting_at=datetime(2026, 3, 20, 12, 0, tzinfo=UTC),
        )
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, -2, -1, 0),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        expected_threshold_date = date(2026, 4, 3)
        for trigger_offset in definition.trigger_offsets:
            evaluation_date = date.fromordinal(
                expected_threshold_date.toordinal() + trigger_offset
            )
            with self.subTest(trigger_offset=trigger_offset):
                result = self.evaluator.evaluate(
                    definition,
                    sailor,
                    self.member_context,
                    evaluation_date,
                )

                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result.threshold_at.isoformat(), "2026-04-03T12:00:00+00:00")
                self.assertEqual(result.threshold_date, expected_threshold_date)
                self.assertEqual(result.trigger_offset, trigger_offset)
                self.assertEqual(
                    result.days_remaining,
                    max((expected_threshold_date - evaluation_date).days, 0),
                )

    def test_hosting_null_baseline_is_excluded(self) -> None:
        sailor = Sailor(discord_id=2, last_hosting_at=None)
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, -2, -1, 0),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        result = self.evaluator.evaluate(
            definition,
            sailor,
            self.member_context,
            date(2026, 4, 1),
        )

        self.assertIsNone(result)

    def test_no_trigger_outside_window(self) -> None:
        sailor = Sailor(
            discord_id=3,
            last_hosting_at=datetime(2026, 3, 20, 12, 0, tzinfo=UTC),
        )
        definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, -2, -1, 0),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )

        result = self.evaluator.evaluate(
            definition,
            sailor,
            self.member_context,
            date(2026, 3, 25),
        )

        self.assertIsNone(result)
