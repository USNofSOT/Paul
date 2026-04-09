import unittest
from datetime import UTC, date, datetime

from src.config.notifications import NOTIFICATION_ROLLOUT
from src.data.models import NotificationEvent
from src.notifications.admin.reporting import (
    build_notification_definitions_embed,
    build_notification_overview_embed,
    build_notification_recent_events_embed,
)
from src.notifications.definitions import DefaultTriggerDefinitionProvider


class TestNotificationReporting(unittest.TestCase):
    def test_build_notification_overview_embed_includes_timings_and_statuses(self) -> None:
        definitions = DefaultTriggerDefinitionProvider().get_definitions()
        recent_event = NotificationEvent(
            id=1,
            notification_type="NO_HOSTING_REMINDER",
            status="pending",
            sailor_id=42,
            ship_role_id=1,
            squad_role_id=None,
            source_activity_at=datetime(2026, 4, 1, 12, 0, tzinfo=UTC),
            source_activity_date=date(2026, 4, 1),
            threshold_at=datetime(2026, 4, 15, 12, 0, tzinfo=UTC),
            threshold_date=date(2026, 4, 15),
            trigger_offset=-1,
            scheduled_for_at=datetime(2026, 4, 14, 12, 0, tzinfo=UTC),
            scheduled_for_date=date(2026, 4, 14),
            destination_channel_id=123,
            payload_snapshot="{}",
            created_at=datetime(2026, 4, 14, 12, 0, tzinfo=UTC),
            updated_at=datetime(2026, 4, 14, 12, 0, tzinfo=UTC),
        )

        embed = build_notification_overview_embed(
            definitions,
            {
                "pending": 1,
                "processing": 0,
                "delivered": 2,
                "failed": 0,
                "skipped": 1,
            },
            [recent_event],
        )

        self.assertEqual(embed.title, "Notification Ops")
        self.assertIn("Notifications evaluator", embed.fields[0].value)
        self.assertIn("NO_VOYAGE_REMINDER", embed.fields[1].value)
        self.assertIn("Pending: **1**", embed.fields[2].value)
        self.assertIn("`#1`", embed.fields[3].value)
        self.assertIn("scheduled=<t:", embed.fields[3].value)

    def test_build_notification_definition_and_recent_event_embeds(self) -> None:
        definitions = DefaultTriggerDefinitionProvider().get_definitions()
        recent_event = NotificationEvent(
            id=7,
            notification_type="NO_VOYAGE_REMINDER",
            status="delivered",
            sailor_id=99,
            ship_role_id=1,
            squad_role_id=None,
            source_activity_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            source_activity_date=date(2026, 3, 1),
            threshold_at=datetime(2026, 3, 29, 12, 0, tzinfo=UTC),
            threshold_date=date(2026, 3, 29),
            trigger_offset=0,
            scheduled_for_at=datetime(2026, 3, 29, 12, 0, tzinfo=UTC),
            scheduled_for_date=date(2026, 3, 29),
            destination_channel_id=123,
            payload_snapshot="{}",
            created_at=datetime(2026, 3, 29, 13, 0, tzinfo=UTC),
            updated_at=datetime(2026, 3, 29, 13, 0, tzinfo=UTC),
        )

        definitions_embed = build_notification_definitions_embed(
            definitions,
            NOTIFICATION_ROLLOUT,
        )
        recent_embed = build_notification_recent_events_embed([recent_event])

        self.assertEqual(definitions_embed.title, "Notification Definitions")
        self.assertTrue(any("Threshold" in field.value for field in definitions_embed.fields))
        self.assertEqual(recent_embed.title, "Recent Notification Events")
        self.assertIn("NO_VOYAGE_REMINDER", recent_embed.description)
