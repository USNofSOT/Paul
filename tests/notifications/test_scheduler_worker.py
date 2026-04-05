import unittest
from datetime import UTC, datetime
from datetime import date
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.ships import BC_VENOM, ROLE_ID_VENOM
from src.data.models import NotificationEvent, Sailor
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.context import build_member_context
from src.notifications.definitions import DefaultTriggerDefinitionProvider
from src.notifications.evaluator import SailorInactivityEligibilityEvaluator
from src.notifications.payloads import NotificationPayloadFactory
from src.notifications.renderer import EmbedNotificationRenderer
from src.notifications.routing import ShipCommandRouteResolver
from src.notifications.scheduler import NotificationSchedulerService
from src.notifications.types import NotificationStatus, NotificationType
from src.notifications.worker import NotificationWorkerService


class DummyRole:
    def __init__(self, role_id: int, name: str) -> None:
        self.id = role_id
        self.name = name


class DummyMember:
    def __init__(self, member_id: int, name: str, roles: list[DummyRole]) -> None:
        self.id = member_id
        self.name = name
        self.display_name = name
        self.roles = roles
        self.display_avatar = type("Avatar", (), {"url": "https://example.com/avatar.png"})()


class DummyChannel:
    def __init__(self, channel_id: int) -> None:
        self.id = channel_id
        self.sent_embeds = []

    async def send(self, embed=None):
        self.sent_embeds.append(embed)


class DummyGuild:
    def __init__(self, member: DummyMember, channel: DummyChannel) -> None:
        self._member = member
        self._channel = channel

    def get_member(self, member_id: int):
        return self._member if self._member.id == member_id else None

    def get_channel(self, channel_id: int):
        return self._channel if self._channel.id == channel_id else None


class DummyBot:
    def __init__(self, guild: DummyGuild) -> None:
        self._guild = guild

    def get_guild(self, guild_id: int):
        del guild_id
        return self._guild


class SuccessfulDeliveryAdapter:
    def __init__(self) -> None:
        self.send = AsyncMock()


class FailingDeliveryAdapter:
    async def send(self, guild, destination_channel_id, rendered):
        del guild, destination_channel_id, rendered
        raise RuntimeError("delivery failed")


class TestNotificationSchedulerAndWorker(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Sailor.__table__.create(self.engine)
        NotificationEvent.__table__.create(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.sailor_repo = SailorRepository()
        self.sailor_repo.session = self.session
        self.event_repo = NotificationEventRepository()
        self.event_repo.session = self.session

        self.ship_role = DummyRole(ROLE_ID_VENOM, "USS Venom")
        self.squad_role = DummyRole(555, "Alpha Squad")
        self.member = DummyMember(1, "Test Sailor", [self.ship_role, self.squad_role])
        self.channel = DummyChannel(BC_VENOM)
        self.bot = DummyBot(DummyGuild(self.member, self.channel))

        sailor = Sailor(
            discord_id=1,
            gamertag="Test Sailor",
            last_voyage_at=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
        )
        self.session.add(sailor)
        self.session.commit()

        self.definition_provider = DefaultTriggerDefinitionProvider()
        self.evaluator = SailorInactivityEligibilityEvaluator()
        self.route_resolver = ShipCommandRouteResolver()
        self.payload_factory = NotificationPayloadFactory()
        self.rollout = {
            NotificationType.NO_VOYAGE_REMINDER: {ROLE_ID_VENOM: ()},
            NotificationType.NO_HOSTING_REMINDER: {},
        }

    def tearDown(self) -> None:
        self.session.close()
        NotificationEvent.__table__.drop(self.engine)
        Sailor.__table__.drop(self.engine)

    async def test_scheduler_reruns_do_not_duplicate_and_worker_delivers_once(self) -> None:
        scheduler = NotificationSchedulerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

        created_first = await scheduler.run_for_date(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())
        created_second = await scheduler.run_for_date(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())

        self.assertEqual(created_first, 1)
        self.assertEqual(created_second, 0)
        self.assertEqual(self.session.query(NotificationEvent).count(), 1)

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = NotificationWorkerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            renderer=EmbedNotificationRenderer(),
            delivery_adapter=delivery_adapter,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

        delivered_first = await worker.run_once(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())
        delivered_second = await worker.run_once(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())

        self.assertEqual(delivered_first, 1)
        self.assertEqual(delivered_second, 0)
        self.assertEqual(delivery_adapter.send.await_count, 1)
        event = self.session.query(NotificationEvent).first()
        self.assertEqual(event.status, NotificationStatus.DELIVERED.value)

    async def test_scheduler_creates_one_event_per_daily_offset_without_duplicates(self) -> None:
        scheduler = NotificationSchedulerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

        created_events = 0
        for evaluation_date in (
                date(2026, 3, 22),
                date(2026, 3, 23),
                date(2026, 3, 24),
                date(2026, 3, 25),
                date(2026, 3, 26),
                date(2026, 3, 27),
                date(2026, 3, 28),
                date(2026, 3, 29),
        ):
            created_events += await scheduler.run_for_date(self.bot, evaluation_date)
            created_events += await scheduler.run_for_date(self.bot, evaluation_date)

        events = (
            self.session.query(NotificationEvent)
            .order_by(NotificationEvent.trigger_offset.asc())
            .all()
        )

        self.assertEqual(created_events, 8)
        self.assertEqual(len(events), 8)
        self.assertEqual(
            [event.trigger_offset for event in events],
            [-7, -6, -5, -4, -3, -2, -1, 0],
        )

    async def test_worker_skips_event_when_activity_cycle_changes(self) -> None:
        scheduler = NotificationSchedulerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )
        await scheduler.run_for_date(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())

        sailor = self.session.query(Sailor).filter(Sailor.discord_id == 1).first()
        sailor.last_voyage_at = datetime(2026, 3, 24, 18, 0, tzinfo=UTC)
        self.session.commit()

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = NotificationWorkerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            renderer=EmbedNotificationRenderer(),
            delivery_adapter=delivery_adapter,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

        delivered = await worker.run_once(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())

        self.assertEqual(delivered, 0)
        self.assertEqual(delivery_adapter.send.await_count, 0)
        event = self.session.query(NotificationEvent).first()
        self.assertEqual(event.status, NotificationStatus.SKIPPED.value)
        self.assertEqual(event.skip_reason, "activity_cycle_changed")

    async def test_worker_alerts_engineers_after_retry_exhaustion(self) -> None:
        scheduler = NotificationSchedulerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )
        await scheduler.run_for_date(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())

        worker = NotificationWorkerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            renderer=EmbedNotificationRenderer(),
            delivery_adapter=FailingDeliveryAdapter(),
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

        with patch("src.notifications.worker.alert_engineers", new=AsyncMock()) as alert_mock:
            await worker.run_once(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())
            await worker.run_once(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())
            await worker.run_once(self.bot, datetime(2026, 3, 24, tzinfo=UTC).date())

        event = self.session.query(NotificationEvent).first()
        self.assertEqual(event.status, NotificationStatus.FAILED.value)
        self.assertEqual(event.attempt_count, 3)
        self.assertEqual(alert_mock.await_count, 1)

    async def test_worker_refreshes_payload_snapshot_with_runtime_wording(self) -> None:
        definition = self.definition_provider.get_definition("NO_VOYAGE_REMINDER")
        sailor = self.sailor_repo.get_sailor(1)
        member_context = build_member_context(self.member)
        eligibility = self.evaluator.evaluate(
            definition,
            sailor,
            member_context,
            date(2026, 3, 29),
        )
        assert eligibility is not None

        original_payload = self.payload_factory.build(
            definition,
            sailor,
            member_context,
            eligibility,
            reference_time=datetime(2026, 3, 29, 9, 0, tzinfo=UTC),
        )
        event, _ = self.event_repo.create_pending_event(
            definition=definition,
            sailor=sailor,
            member_context=member_context,
            eligibility=eligibility,
            destination_channel_id=BC_VENOM,
            payload_snapshot=self.payload_factory.to_snapshot(original_payload),
        )
        self.assertIn("is due", event.payload_snapshot)

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = NotificationWorkerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            renderer=EmbedNotificationRenderer(),
            delivery_adapter=delivery_adapter,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

        with patch("src.notifications.worker.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = datetime(2026, 3, 29, 15, 0, tzinfo=UTC)
            delivered = await worker.run_once(self.bot, date(2026, 3, 29))

        refreshed_event = self.session.query(NotificationEvent).first()
        self.assertEqual(delivered, 1)
        self.assertIn("became due", refreshed_event.payload_snapshot)
        self.assertEqual(refreshed_event.status, NotificationStatus.DELIVERED.value)
