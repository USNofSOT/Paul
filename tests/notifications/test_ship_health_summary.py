import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.main_server import BOT_TEST_COMMAND
from src.config.ships import BC_VENOM, ROLE_ID_VENOM
from src.data.models import Hosted, Sailor, VoyageType, Voyages
from src.data.repository.ship_health_summary_repository import ShipHealthSummaryRepository
from src.notifications.routing import ShipCommandRouteResolver
from src.notifications.ship_health_summary import (
    DatabaseShipHealthSummaryDataProvider,
    ShipHealthSummaryEmbedRenderer,
    ShipHealthSummaryService,
)


class DummyMember:
    def __init__(self, member_id: int, roles: list["DummyRole"]) -> None:
        self.id = member_id
        self.roles = roles


class DummyRole:
    def __init__(self, role_id: int, name: str, members: list[DummyMember] | None = None) -> None:
        self.id = role_id
        self.name = name
        self.members = members or []


class DummyChannel:
    def __init__(self, channel_id: int) -> None:
        self.id = channel_id


class DummyGuild:
    def __init__(self, *, role: DummyRole | None, channels: dict[int, object]) -> None:
        self._role = role
        self._channels = channels

    def get_role(self, role_id: int):
        if self._role and self._role.id == role_id:
            return self._role
        return None

    def get_channel(self, channel_id: int):
        return self._channels.get(channel_id)


class DummyBot:
    def __init__(self, guild: DummyGuild) -> None:
        self._guild = guild

    def get_guild(self, guild_id: int):
        del guild_id
        return self._guild


class SuccessfulDeliveryAdapter:
    def __init__(self) -> None:
        self.send = AsyncMock()


class TestShipHealthSummary(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Sailor.__table__.create(self.engine)
        Voyages.__table__.create(self.engine)
        Hosted.__table__.create(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.repository = ShipHealthSummaryRepository()
        self.repository.session = self.session
        self.repository.get_ship_size_on_or_before = lambda **kwargs: 7
        self.reference_time = datetime(2026, 4, 9, 12, 0, tzinfo=UTC)

        sailors = [
            Sailor(
                discord_id=1,
                gamertag="Due Soon Voyage",
                last_voyage_at=self.reference_time - timedelta(days=27),
            ),
            Sailor(
                discord_id=2,
                gamertag="Overdue Voyage",
                last_voyage_at=self.reference_time - timedelta(days=30),
            ),
            Sailor(
                discord_id=3,
                gamertag="Due Soon Hosting",
                last_hosting_at=self.reference_time - timedelta(days=13),
            ),
            Sailor(
                discord_id=4,
                gamertag="Overdue Hosting",
                last_hosting_at=self.reference_time - timedelta(days=15),
            ),
            Sailor(
                discord_id=5,
                gamertag="No Baselines",
                last_voyage_at=None,
                last_hosting_at=None,
            ),
        ]
        self.session.add_all(sailors)
        self.session.add_all(
            [
                Voyages(
                    log_id=100,
                    target_id=1,
                    log_time=self.reference_time - timedelta(days=1),
                    ship_role_id=ROLE_ID_VENOM,
                ),
                Voyages(
                    log_id=101,
                    target_id=2,
                    log_time=self.reference_time - timedelta(days=3),
                    ship_role_id=ROLE_ID_VENOM,
                ),
                Voyages(
                    log_id=102,
                    target_id=2,
                    log_time=self.reference_time - timedelta(days=9),
                    ship_role_id=ROLE_ID_VENOM,
                ),
                Hosted(
                    log_id=200,
                    target_id=3,
                    log_time=self.reference_time - timedelta(days=2),
                    ship_role_id=ROLE_ID_VENOM,
                    voyage_type=VoyageType.UNKNOWN,
                ),
                Hosted(
                    log_id=201,
                    target_id=4,
                    log_time=self.reference_time - timedelta(days=10),
                    ship_role_id=ROLE_ID_VENOM,
                    voyage_type=VoyageType.UNKNOWN,
                ),
            ]
        )
        self.session.commit()

        self.ship_role = DummyRole(ROLE_ID_VENOM, "USS Venom")
        self.alpha_squad = DummyRole(9001, "Alpha Squad")
        self.bravo_squad = DummyRole(9002, "Bravo Squad")
        members = [
            DummyMember(1, [self.ship_role, self.alpha_squad]),
            DummyMember(2, [self.ship_role, self.alpha_squad]),
            DummyMember(3, [self.ship_role, self.bravo_squad]),
            DummyMember(4, [self.ship_role, self.bravo_squad]),
            DummyMember(5, [self.ship_role]),
        ]
        self.ship_role.members = members
        self.guild = DummyGuild(
            role=self.ship_role,
            channels={
                BC_VENOM: DummyChannel(BC_VENOM),
                BOT_TEST_COMMAND: DummyChannel(BOT_TEST_COMMAND),
            },
        )
        self.bot = DummyBot(self.guild)

    def tearDown(self) -> None:
        self.session.close()
        Hosted.__table__.drop(self.engine)
        Voyages.__table__.drop(self.engine)
        Sailor.__table__.drop(self.engine)

    def test_data_provider_counts_due_soon_overdue_and_recent_activity(self) -> None:
        provider = DatabaseShipHealthSummaryDataProvider(self.repository)

        summary = provider.build_summary(
            ship_role_id=ROLE_ID_VENOM,
            ship_name="USS Venom",
            ship_size=5,
            squad_memberships={
                "Alpha Squad": [1, 2],
                "Bravo Squad": [3, 4],
            },
            sailor_ids=[1, 2, 3, 4, 5],
            reference_time=self.reference_time,
        )

        self.assertEqual(summary.ship_size, 5)
        self.assertEqual(summary.ship_size_delta, -2)
        self.assertEqual(summary.voyaging_due_soon_count, 1)
        self.assertEqual(summary.voyaging_overdue_count, 1)
        self.assertEqual(summary.hosting_due_soon_count, 1)
        self.assertEqual(summary.hosting_overdue_count, 1)
        self.assertEqual(summary.recent_voyage_count, 2)
        self.assertEqual(summary.recent_voyage_delta, 1)
        self.assertEqual(summary.recent_hosting_count, 1)
        self.assertEqual(summary.recent_hosting_delta, 0)
        self.assertEqual(
            [
                (squad.squad_name, squad.overdue_member_ids)
                for squad in summary.squad_summaries
            ],
            [("Alpha Squad", (2,)), ("Bravo Squad", (4,))],
        )

    def test_renderer_uses_ship_emoji_and_compact_sections(self) -> None:
        rendered = ShipHealthSummaryEmbedRenderer().render(
            DatabaseShipHealthSummaryDataProvider(self.repository).build_summary(
                ship_role_id=ROLE_ID_VENOM,
                ship_name="USS Venom",
                ship_size=5,
                squad_memberships={
                    "Alpha Squad": [1, 2],
                    "Bravo Squad": [3, 4],
                },
                sailor_ids=[1, 2, 3, 4, 5],
                reference_time=self.reference_time,
            )
        )

        self.assertEqual(rendered.embed_title, "<:Venom:1239895956489633852> Ship health summary")
        self.assertEqual(rendered.embed_description, "Weekly operational overview for USS Venom.")
        self.assertEqual(
            [field.name for field in rendered.fields],
            ["👥 Crew", "⚓ Recent Activity", "🧭 Squads"],
        )
        self.assertIn("5 (-2)", rendered.fields[0].value)
        self.assertIn("2 (+1)", rendered.fields[1].value)
        self.assertIn("Alpha Squad", rendered.fields[2].value)
        self.assertIn("  - <@2>", rendered.fields[2].value)
        self.assertIn("  - <@4>", rendered.fields[2].value)
        self.assertEqual(
            rendered.image_attachment_filename,
            "ship_health_summary_chart.png",
        )
        self.assertIsNotNone(rendered.image_attachment_bytes)
        self.assertEqual(rendered.footer, "Automated weekly command summary")

    async def test_service_sends_one_summary_per_enabled_ship(self) -> None:
        delivery_adapter = SuccessfulDeliveryAdapter()
        service = ShipHealthSummaryService(
            data_provider=DatabaseShipHealthSummaryDataProvider(self.repository),
            renderer=ShipHealthSummaryEmbedRenderer(),
            route_resolver=ShipCommandRouteResolver(),
            delivery_adapter=delivery_adapter,
            enabled=True,
            rollout=(ROLE_ID_VENOM,),
        )

        summary = await service.run_once(self.bot, reference_time=self.reference_time)

        self.assertEqual(summary.summary_count, 1)
        self.assertEqual(summary.skipped_count, 0)
        self.assertEqual(summary.per_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(delivery_adapter.send.await_count, 1)

    async def test_service_skips_ship_when_command_channel_missing(self) -> None:
        delivery_adapter = SuccessfulDeliveryAdapter()
        unroutable_bot = DummyBot(
            DummyGuild(
                role=self.ship_role,
                channels={BOT_TEST_COMMAND: DummyChannel(BOT_TEST_COMMAND)},
            )
        )
        service = ShipHealthSummaryService(
            data_provider=DatabaseShipHealthSummaryDataProvider(self.repository),
            renderer=ShipHealthSummaryEmbedRenderer(),
            route_resolver=ShipCommandRouteResolver(),
            delivery_adapter=delivery_adapter,
            enabled=True,
            rollout=(ROLE_ID_VENOM,),
        )

        summary = await service.run_once(unroutable_bot, reference_time=self.reference_time)

        self.assertEqual(summary.summary_count, 0)
        self.assertEqual(summary.skipped_count, 1)
        self.assertEqual(summary.skipped_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(delivery_adapter.send.await_count, 0)

    async def test_service_ignores_non_enabled_ships(self) -> None:
        delivery_adapter = SuccessfulDeliveryAdapter()
        service = ShipHealthSummaryService(
            data_provider=DatabaseShipHealthSummaryDataProvider(self.repository),
            renderer=ShipHealthSummaryEmbedRenderer(),
            route_resolver=ShipCommandRouteResolver(),
            delivery_adapter=delivery_adapter,
            enabled=True,
            rollout=(),
        )

        summary = await service.run_once(self.bot, reference_time=self.reference_time)

        self.assertEqual(summary.summary_count, 0)
        self.assertEqual(summary.skipped_count, 0)
        self.assertEqual(delivery_adapter.send.await_count, 0)
