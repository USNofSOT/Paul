import unittest
from datetime import UTC, date, datetime

from src.config.requirements import HOSTING_REQUIREMENT_IN_DAYS
from src.config.ships import BC_TITAN
from src.data.models import Sailor
from src.notifications.payloads import NotificationPayloadFactory
from src.notifications.renderer import EmbedNotificationRenderer
from src.notifications.rollout import is_notification_enabled_for_member
from src.notifications.routing import ShipCommandRouteResolver
from src.notifications.types import (
    EligibilityResult,
    NotificationDefinition,
    NotificationType,
    RoutingTargetType,
    TemplateKey,
    ResolvedMemberContext,
)


class DummyGuild:
    def __init__(self, channels: dict[int, object]) -> None:
        self.channels = channels

    def get_channel(self, channel_id: int):
        return self.channels.get(channel_id)


class TestRenderingAndRouting(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = NotificationDefinition(
            notification_type=NotificationType.NO_HOSTING_REMINDER,
            activity_field="last_hosting_at",
            threshold_days=HOSTING_REQUIREMENT_IN_DAYS,
            trigger_offsets=(-3, -2, -1, 0),
            template_key=TemplateKey.NO_HOSTING_REMINDER,
            routing_target=RoutingTargetType.SHIP_COMMAND_CHANNEL,
        )
        self.member_context = ResolvedMemberContext(
            sailor_id=1,
            display_name="Render Sailor",
            ship_role_id=1237838106711822457,
            ship_name="USS Venom",
            squad_role_id=10,
            squad_name="Alpha Squad",
            avatar_url="https://example.com/avatar.png",
        )
        self.sailor = Sailor(discord_id=1, gamertag="Render Sailor")
        self.eligibility = EligibilityResult(
            source_activity_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
            source_activity_date=date(2026, 3, 20),
            threshold_at=datetime(2026, 4, 3, 8, 0, tzinfo=UTC),
            threshold_date=date(2026, 4, 3),
            trigger_offset=-3,
            scheduled_for_date=date(2026, 3, 31),
            days_remaining=3,
        )

    def test_payload_snapshot_round_trip_and_rendering(self) -> None:
        factory = NotificationPayloadFactory()
        payload = factory.build(
            self.definition,
            self.sailor,
            self.member_context,
            self.eligibility,
            reference_time=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )
        snapshot = factory.to_snapshot(payload)
        restored = factory.from_snapshot(snapshot)
        rendered = EmbedNotificationRenderer().render(restored)
        embed = EmbedNotificationRenderer.to_embed(rendered)

        self.assertEqual(restored.title, "<:Venom:1239895956489633852> Hosting inactivity reminder")
        self.assertIn("<@1> Render Sailor is due <t:", restored.body)
        self.assertIn(":R>", restored.body)
        self.assertIn(
            f"for reaching {HOSTING_REQUIREMENT_IN_DAYS} days without hosting.",
            restored.body,
        )
        self.assertEqual(rendered.embed_title, restored.title)
        self.assertEqual(
            rendered.footer,
            "NO_HOSTING_REMINDER",
        )
        self.assertGreater(rendered.color_value, 0)
        self.assertEqual(rendered.thumbnail_url, "https://example.com/avatar.png")
        self.assertIn("<t:", restored.source_activity_date)
        self.assertEqual(restored.display_fields, ())
        self.assertEqual(rendered.fields, ())
        self.assertIsNone(embed.author.name)

    def test_payload_uses_became_due_after_threshold_time(self) -> None:
        payload = NotificationPayloadFactory().build(
            self.definition,
            self.sailor,
            self.member_context,
            self.eligibility,
            reference_time=datetime(2026, 4, 3, 9, 0, tzinfo=UTC),
        )

        self.assertIn("<@1> Render Sailor became due <t:", payload.body)
        self.assertIn(":R>", payload.body)

    def test_payload_sanitizes_subject_name(self) -> None:
        risky_context = ResolvedMemberContext(
            sailor_id=1,
            display_name="@everyone *Render* Sailor",
            ship_role_id=1237838106711822457,
            ship_name="USS Venom",
            squad_role_id=10,
            squad_name="Alpha Squad",
            avatar_url=None,
        )

        payload = NotificationPayloadFactory().build(
            self.definition,
            self.sailor,
            risky_context,
            self.eligibility,
            reference_time=datetime(2026, 4, 1, 8, 0, tzinfo=UTC),
        )

        self.assertIn("<@1>", payload.body)
        self.assertNotIn("@everyone", payload.body)
        self.assertIn("@\u200beveryone", payload.body)

    def test_route_resolver_skips_when_command_channel_missing(self) -> None:
        route = ShipCommandRouteResolver().resolve(
            self.definition,
            self.member_context,
            DummyGuild(channels={}),
        )

        self.assertIsNone(route.destination_channel_id)
        self.assertEqual(route.skip_reason, "command_channel_not_found")

    def test_route_resolver_uses_ship_command_channel_for_titan(self) -> None:
        titan_context = ResolvedMemberContext(
            sailor_id=2,
            display_name="Titan Sailor",
            ship_role_id=1247405133130764329,
            ship_name="USS Titan",
            squad_role_id=None,
            squad_name=None,
            avatar_url=None,
        )

        route = ShipCommandRouteResolver().resolve(
            self.definition,
            titan_context,
            DummyGuild(channels={BC_TITAN: object()}),
        )

        self.assertEqual(route.destination_channel_id, BC_TITAN)
        self.assertIsNone(route.skip_reason)

    def test_rollout_honors_ship_and_squad_scope(self) -> None:
        enabled = is_notification_enabled_for_member(
            {NotificationType.NO_HOSTING_REMINDER: {1237838106711822457: (10,)}},
            NotificationType.NO_HOSTING_REMINDER,
            self.member_context,
        )
        disabled = is_notification_enabled_for_member(
            {NotificationType.NO_HOSTING_REMINDER: {1237838106711822457: (999,)}},
            NotificationType.NO_HOSTING_REMINDER,
            self.member_context,
        )

        self.assertTrue(enabled)
        self.assertFalse(disabled)
