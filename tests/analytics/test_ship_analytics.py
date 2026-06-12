from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.ranges import TimeRange
from src.analytics.ship_analytics import ShipAnalyticsFilters, ShipAnalyticsService
from src.data.models import Hosted, Sailor, Voyages, VoyageType


def _session():
    engine = create_engine("sqlite:///:memory:")
    for table in (
            Sailor.__table__,
            Hosted.__table__,
            Voyages.__table__,
    ):
        table.create(engine)
    return sessionmaker(bind=engine)()


def _seed(session, reference_time):
    session.add_all(
        [
            Sailor(discord_id=1, gamertag="Host"),
            Sailor(discord_id=2, gamertag="Crew"),
            Sailor(discord_id=3, gamertag="Other"),
            Sailor(discord_id=4, gamertag="Fourth"),
            Sailor(discord_id=5, gamertag="Fifth"),
        ]
    )
    session.add_all(
        [
            Hosted(
                log_id=100,
                target_id=1,
                log_time=reference_time - timedelta(days=1),
                ship_role_id=500,
                ship_name="USS Test",
                voyage_type=VoyageType.SKIRMISH,
                gold_count=100,
            ),
            Hosted(
                log_id=101,
                target_id=3,
                log_time=reference_time - timedelta(days=3),
                ship_role_id=600,
                ship_name="USS Other",
                auxiliary_ship_name="USS Aux",
                voyage_type=VoyageType.PATROL,
                gold_count=50,
            ),
            Hosted(
                log_id=102,
                target_id=1,
                log_time=reference_time - timedelta(days=120),
                ship_role_id=500,
                ship_name="USS Test",
                voyage_type=VoyageType.ADVENTURE,
                gold_count=25,
            ),
        ]
    )
    session.add_all(
        [
            Voyages(
                log_id=100,
                target_id=2,
                log_time=reference_time - timedelta(days=1),
                ship_role_id=500,
            ),
            Voyages(
                log_id=100,
                target_id=3,
                log_time=reference_time - timedelta(days=1),
                ship_role_id=500,
            ),
            Voyages(
                log_id=101,
                target_id=2,
                log_time=reference_time - timedelta(days=3),
                ship_role_id=600,
            ),
        ]
    )
    session.commit()


def test_ship_activity_filters_by_role_fleet_and_voyage_type():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    summary = ShipAnalyticsService(session).build_activity(
        ShipAnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            ship_role_id=500,
            fleet_role_ids=(500, 600),
            voyage_type=VoyageType.SKIRMISH,
        )
    )

    assert summary.total_hosted == 1
    assert summary.total_voyages == 2
    assert summary.ship_rows[0].ship_role_id == 500
    assert summary.ship_rows[0].hosted == 1
    assert summary.ship_rows[0].voyages == 2
    assert summary.voyage_type_counts == {VoyageType.SKIRMISH: 1}
    assert summary.unique_voyage_logs == 1


def test_ship_history_filters_by_ship_name_host_crew_and_type():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    summary = ShipAnalyticsService(session).build_history(
        ShipAnalyticsFilters(
            time_range=TimeRange.from_reference("30d", reference_time),
            ship_name="USS Test",
            host_id=1,
            crew_member_id=2,
            voyage_type=VoyageType.SKIRMISH,
        )
    )

    assert summary.total_logs == 1
    assert summary.total_gold == 100
    assert summary.top_hosts == [(1, 1)]
    assert summary.recent_logs == [100]


def test_ship_activity_all_time_includes_rows_older_than_five_years():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    old_time = reference_time - timedelta(days=2200)
    session.add_all(
        [
            Hosted(
                log_id=900,
                target_id=1,
                log_time=old_time,
                ship_role_id=500,
                ship_name="USS Test",
                voyage_type=VoyageType.CONVOY,
            ),
            Voyages(
                log_id=900,
                target_id=2,
                log_time=old_time,
                ship_role_id=500,
            ),
        ]
    )
    session.commit()

    summary = ShipAnalyticsService(session).build_activity(
        ShipAnalyticsFilters(time_range=TimeRange.from_reference("all", reference_time))
    )

    assert summary.total_hosted == 4
    assert summary.total_voyages == 4
    assert summary.bucket_series[0].start == datetime(old_time.year, old_time.month, 1)


def test_ship_activity_tracks_common_companion_pairs():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    session.add(
        Hosted(
            log_id=103,
            target_id=1,
            log_time=reference_time - timedelta(days=2),
            ship_role_id=500,
            ship_name="USS Test",
            voyage_type=VoyageType.SKIRMISH,
        )
    )
    session.add_all(
        [
            Voyages(
                log_id=103,
                target_id=2,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=500,
            ),
            Voyages(
                log_id=103,
                target_id=3,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=500,
            ),
        ]
    )
    session.commit()

    summary = ShipAnalyticsService(session).build_activity(
        ShipAnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            ship_role_id=500,
        )
    )

    assert summary.unique_voyage_logs == 2
    assert summary.top_companion_pairs[0].user_one_id == 2
    assert summary.top_companion_pairs[0].user_two_id == 3
    assert summary.top_companion_pairs[0].shared_voyages == 2


def test_ship_activity_tracks_common_ship_pairs_from_filtered_logs():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    session.add(
        Hosted(
            log_id=104,
            target_id=1,
            log_time=reference_time - timedelta(days=2),
            ship_role_id=500,
            ship_name="USS Test",
            voyage_type=VoyageType.SKIRMISH,
        )
    )
    session.add_all(
        [
            Voyages(
                log_id=104,
                target_id=2,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=500,
            ),
            Voyages(
                log_id=104,
                target_id=3,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=600,
            ),
        ]
    )
    session.commit()

    summary = ShipAnalyticsService(session).build_activity(
        ShipAnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            ship_role_id=500,
        )
    )

    assert summary.top_ship_pairs[0].ship_one_role_id == 500
    assert summary.top_ship_pairs[0].ship_two_role_id == 600
    assert summary.top_ship_pairs[0].shared_voyages == 1


def test_ship_activity_tracks_ship_pairings_by_participant_rows():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    session.add_all(
        [
            Voyages(
                log_id=100,
                target_id=4,
                log_time=reference_time - timedelta(days=1),
                ship_role_id=500,
            ),
            Hosted(
                log_id=104,
                target_id=1,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=500,
                ship_name="USS Test",
                voyage_type=VoyageType.SKIRMISH,
            ),
            Voyages(
                log_id=104,
                target_id=2,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=500,
            ),
            Voyages(
                log_id=104,
                target_id=3,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=600,
            ),
            Voyages(
                log_id=104,
                target_id=5,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=-1,
            ),
        ]
    )
    session.commit()

    summary = ShipAnalyticsService(session).build_activity(
        ShipAnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            ship_role_id=500,
        )
    )

    assert summary.ship_pairing_participants == 5
    assert summary.top_ship_pairings[0].ship_role_ids == (500,)
    assert summary.top_ship_pairings[0].participant_count == 3
    assert summary.top_ship_pairings[1].ship_role_ids == (500, 600)
    assert summary.top_ship_pairings[1].participant_count == 2


def test_ship_activity_limits_pairing_lists_to_five():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    session.add(
        Hosted(
            log_id=105,
            target_id=1,
            log_time=reference_time - timedelta(days=2),
            ship_role_id=500,
            ship_name="USS Test",
            voyage_type=VoyageType.SKIRMISH,
        )
    )
    session.add_all(
        [
            Voyages(
                log_id=105,
                target_id=2,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=600,
            ),
            Voyages(
                log_id=105,
                target_id=3,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=700,
            ),
            Voyages(
                log_id=105,
                target_id=4,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=800,
            ),
            Voyages(
                log_id=105,
                target_id=5,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=900,
            ),
        ]
    )
    session.commit()

    summary = ShipAnalyticsService(session).build_activity(
        ShipAnalyticsFilters(time_range=TimeRange.from_reference("7d", reference_time))
    )

    assert len(summary.top_companion_pairs) == 5
    assert len(summary.top_ship_pairs) == 5
