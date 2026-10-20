import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models import (
    Hosted,
    RoleChangeLog,
    RoleChangeType,
    RoleSize,
    RoleType,
    Sailor,
    Voyages,
    VoyageType,
)
from src.data.repository.ship_briefing_repository import ShipBriefingRepository


class TestShipBriefingRepository(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        for table in (
            Sailor.__table__,
            Hosted.__table__,
            Voyages.__table__,
            RoleChangeLog.__table__,
        ):
            table.create(self.engine)
        with self.engine.begin() as connection:
            connection.exec_driver_sql(
                """
                CREATE TABLE role_size (
                    id INTEGER NOT NULL,
                    role_id BIGINT NOT NULL,
                    role_type VARCHAR(4) NOT NULL,
                    member_count INTEGER NOT NULL,
                    log_time DATETIME NOT NULL,
                    PRIMARY KEY (id, role_id)
                )
                """
            )
        session = sessionmaker(bind=self.engine)()
        self.repository = ShipBriefingRepository()
        self.repository.session = session
        self.now = datetime(2026, 7, 24, 15)
        session.add(Sailor(discord_id=1, gamertag="Sailor"))
        session.add_all(
            (
                Hosted(
                    log_id=100,
                    target_id=1,
                    log_time=self.now - timedelta(days=10),
                    ship_role_id=500,
                    voyage_type=VoyageType.UNKNOWN,
                    voyage_planning_message_id=123,
                ),
                Hosted(
                    log_id=101,
                    target_id=1,
                    log_time=self.now - timedelta(days=1),
                    ship_role_id=500,
                    voyage_type=VoyageType.UNKNOWN,
                ),
                Voyages(
                    log_id=100,
                    target_id=1,
                    log_time=self.now - timedelta(days=10),
                    ship_role_id=500,
                ),
                Voyages(
                    log_id=101,
                    target_id=1,
                    log_time=self.now - timedelta(days=1),
                    ship_role_id=500,
                ),
                RoleChangeLog(
                    target_id=1,
                    guild_id=999,
                    log_time=self.now - timedelta(days=20),
                    change_type=RoleChangeType.ADDED,
                    role_id=500,
                    role_name="USS Test",
                ),
                RoleSize(
                    id=1,
                    role_id=500,
                    role_type=RoleType.SHIP,
                    member_count=9,
                    log_time=self.now - timedelta(days=2),
                ),
            )
        )
        session.commit()

    def tearDown(self):
        self.repository.close_session()
        self.engine.dispose()

    def test_reads_activity_and_trends_directly_from_log_tables(self):
        self.assertEqual(
            self.repository.get_latest_voyage_activity([1])[1],
            self.now - timedelta(days=1),
        )
        self.assertEqual(
            self.repository.get_latest_hosting_activity([1])[1],
            self.now - timedelta(days=1),
        )
        self.assertEqual(
            self.repository.get_latest_ship_role_additions(
                ship_role_id=500,
                sailor_ids=[1],
            )[1],
            self.now - timedelta(days=20),
        )
        self.assertEqual(self.repository.get_public_service_counts([1]), {1: 1})
        self.assertEqual(
            self.repository.count_voyage_logs_between(
                ship_role_id=500,
                start=self.now - timedelta(days=7),
                end=self.now,
            ),
            1,
        )
        self.assertEqual(
            self.repository.count_hosting_logs_between(
                ship_role_id=500,
                start=self.now - timedelta(days=7),
                end=self.now,
            ),
            1,
        )
        self.assertEqual(
            self.repository.get_ship_size_on_or_before(
                ship_role_id=500,
                before=self.now,
            ),
            9,
        )
