import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.main_server import BOT_TEST_COMMAND
from src.config.notifications import (
    NOTIFICATION_DELIVERY_GRACE_HOURS,
    NOTIFICATION_LOOKAHEAD_HOURS,
)
from src.config.ships import BC_VENOM, ROLE_ID_VENOM
from src.data.models import NotificationEvent, Sailor
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
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
    def __init__(self, member: DummyMember, channel: DummyChannel, test_channel: DummyChannel) -> None:
        self._member = member
        self._channel = channel
        self._test_channel = test_channel

    def get_member(self, member_id: int):
        return self._member if self._member.id == member_id else None

    def get_channel(self, channel_id: int):
        if self._channel.id == channel_id:
            return self._channel
        if self._test_channel.id == channel_id:
            return self._test_channel
        return None


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
        self.test_channel = DummyChannel(BOT_TEST_COMMAND)
        self.bot = DummyBot(DummyGuild(self.member, self.channel, self.test_channel))

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

    def _build_scheduler(self) -> NotificationSchedulerService:
        return NotificationSchedulerService(
            definition_provider=self.definition_provider,
            eligibility_evaluator=self.evaluator,
            route_resolver=self.route_resolver,
            event_repository=self.event_repo,
            sailor_repository=self.sailor_repo,
            payload_factory=self.payload_factory,
            rollout_map=self.rollout,
        )

    def _build_worker(self, delivery_adapter) -> NotificationWorkerService:
        return NotificationWorkerService(
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

    async def test_scheduler_precreates_exact_time_events_without_duplicates(self) -> None:
        scheduler = self._build_scheduler()

        first = await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
            lookahead_hours=NOTIFICATION_LOOKAHEAD_HOURS,
        )
        second = await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 25, 12, 0, tzinfo=UTC),
            lookahead_hours=NOTIFICATION_LOOKAHEAD_HOURS,
        )
        duplicate = await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 25, 12, 0, tzinfo=UTC),
            lookahead_hours=NOTIFICATION_LOOKAHEAD_HOURS,
        )

        events = (
            self.session.query(NotificationEvent)
            .order_by(NotificationEvent.scheduled_for_at.asc())
            .all()
        )

        self.assertEqual(first.event_count, 1)
        self.assertEqual(second.event_count, 1)
        self.assertEqual(duplicate.event_count, 0)
        self.assertEqual(first.per_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(second.per_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(len(events), 2)
        self.assertEqual(
            [event.trigger_offset for event in events],
            [-7, -3],
        )
        self.assertEqual(
            [event.scheduled_for_at.isoformat() for event in events],
            [
                "2026-03-22T12:00:00",
                "2026-03-26T12:00:00",
            ],
        )

    async def test_scheduler_precreates_single_seven_day_overdue_event(self) -> None:
        scheduler = self._build_scheduler()

        summary = await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 4, 5, 0, 30, tzinfo=UTC),
            lookahead_hours=NOTIFICATION_LOOKAHEAD_HOURS,
        )

        events = (
            self.session.query(NotificationEvent)
            .order_by(NotificationEvent.scheduled_for_at.asc())
            .all()
        )

        self.assertEqual(summary.event_count, 1)
        self.assertEqual(summary.per_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trigger_offset, 7)
        self.assertEqual(events[0].scheduled_for_at.isoformat(), "2026-04-05T12:00:00")

    async def test_worker_delivers_only_due_events(self) -> None:
        scheduler = self._build_scheduler()
        await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = self._build_worker(delivery_adapter)

        early = await worker.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 22, 11, 59, tzinfo=UTC),
        )
        due = await worker.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 22, 12, 5, tzinfo=UTC),
        )

        self.assertEqual(early.event_count, 0)
        self.assertEqual(due.event_count, 1)
        self.assertEqual(due.per_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(delivery_adapter.send.await_count, 1)

    async def test_worker_skips_events_after_grace_window_elapses(self) -> None:
        scheduler = self._build_scheduler()
        await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )

        worker = self._build_worker(SuccessfulDeliveryAdapter())
        summary = await worker.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 22, 12, 0, tzinfo=UTC)
                           + timedelta(hours=NOTIFICATION_DELIVERY_GRACE_HOURS, minutes=1),
        )

        event = self.session.query(NotificationEvent).order_by(NotificationEvent.id.asc()).first()
        self.assertEqual(summary.event_count, 0)
        self.assertEqual(event.status, NotificationStatus.SKIPPED.value)
        self.assertEqual(event.skip_reason, "delivery_window_elapsed")

    async def test_worker_skips_event_when_activity_cycle_changes(self) -> None:
        scheduler = self._build_scheduler()
        await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )

        sailor = self.session.query(Sailor).filter(Sailor.discord_id == 1).first()
        sailor.last_voyage_at = datetime(2026, 3, 24, 18, 0, tzinfo=UTC)
        self.session.commit()

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = self._build_worker(delivery_adapter)
        summary = await worker.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 22, 12, 5, tzinfo=UTC),
        )

        self.assertEqual(summary.event_count, 0)
        self.assertEqual(delivery_adapter.send.await_count, 0)
        event = self.session.query(NotificationEvent).order_by(NotificationEvent.id.asc()).first()
        self.assertEqual(event.status, NotificationStatus.SKIPPED.value)
        self.assertEqual(event.skip_reason, "activity_cycle_changed")

    async def test_worker_alerts_engineers_after_retry_exhaustion(self) -> None:
        scheduler = self._build_scheduler()
        await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )

        worker = self._build_worker(FailingDeliveryAdapter())
        due_time = datetime(2026, 3, 22, 12, 5, tzinfo=UTC)

        with patch("src.notifications.worker.alert_engineers", new=AsyncMock()) as alert_mock:
            await worker.run_once(self.bot, reference_time=due_time)
            await worker.run_once(self.bot, reference_time=due_time + timedelta(minutes=5))
            await worker.run_once(self.bot, reference_time=due_time + timedelta(minutes=10))

        event = self.session.query(NotificationEvent).order_by(NotificationEvent.id.asc()).first()
        self.assertEqual(event.status, NotificationStatus.FAILED.value)
        self.assertEqual(event.attempt_count, 3)
        self.assertEqual(alert_mock.await_count, 1)
        fields = alert_mock.await_args.kwargs["fields"]
        self.assertTrue(any(field.label == "Ship Overview" for field in fields))

    async def test_worker_refreshes_payload_snapshot_with_runtime_wording(self) -> None:
        scheduler = self._build_scheduler()
        await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 28, 0, 0, tzinfo=UTC),
        )

        event = self.session.query(NotificationEvent).order_by(NotificationEvent.id.asc()).first()
        self.assertIn("is due", event.payload_snapshot)

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = self._build_worker(delivery_adapter)
        summary = await worker.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 29, 15, 0, tzinfo=UTC),
            batch_size=10,
        )

        refreshed_event = self.session.query(NotificationEvent).filter(
            NotificationEvent.id == event.id
        ).first()
        self.assertEqual(summary.event_count, 1)
        self.assertIn("became due", refreshed_event.payload_snapshot)
        self.assertEqual(refreshed_event.status, NotificationStatus.DELIVERED.value)

    async def test_worker_renders_overdue_status_for_seven_day_overdue_event(self) -> None:
        scheduler = self._build_scheduler()
        await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 4, 5, 0, 0, tzinfo=UTC),
        )

        delivery_adapter = SuccessfulDeliveryAdapter()
        worker = self._build_worker(delivery_adapter)
        summary = await worker.run_once(
            self.bot,
            reference_time=datetime(2026, 4, 5, 12, 5, tzinfo=UTC),
            batch_size=10,
        )

        refreshed_event = self.session.query(NotificationEvent).order_by(
            NotificationEvent.id.asc()
        ).first()
        self.assertEqual(summary.event_count, 1)
        self.assertIn("became due", refreshed_event.payload_snapshot)
        self.assertIn("7 day(s) overdue", refreshed_event.payload_snapshot)
        self.assertEqual(refreshed_event.status, NotificationStatus.DELIVERED.value)

    async def test_scheduler_counts_ships_in_summary(self) -> None:
        scheduler = self._build_scheduler()
        first = await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )
        second = await scheduler.run_once(
            self.bot,
            reference_time=datetime(2026, 3, 25, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(first.per_ship_counts, {ROLE_ID_VENOM: 1})
        self.assertEqual(second.per_ship_counts, {ROLE_ID_VENOM: 1})

    async def test_scheduler_records_skipped_event_when_route_missing(self) -> None:
        scheduler = self._build_scheduler()
        unroutable_bot = DummyBot(
            DummyGuild(
                self.member,
                DummyChannel(999999),
                DummyChannel(888888),
            )
        )

        summary = await scheduler.run_once(
            unroutable_bot,
            reference_time=datetime(2026, 3, 21, 12, 0, tzinfo=UTC),
        )

        event = self.session.query(NotificationEvent).order_by(NotificationEvent.id.asc()).first()
        self.assertEqual(summary.event_count, 1)
        self.assertEqual(event.status, NotificationStatus.SKIPPED.value)
        self.assertEqual(event.skip_reason, "command_channel_not_found")
