from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.voyage_analytics import (
    AnalyticsFilters,
    TimeRange,
    VoyageAnalyticsService,
    bucket_start_for,
    resolve_time_range,
)
from src.data.models import (
    Hosted,
    Rank,
    Sailor,
    Subclasses,
    SubclassType,
    Voyages,
    VoyageType,
)


def _session():
    engine = create_engine("sqlite:///:memory:")
    for table in (
            Rank.__table__,
            Sailor.__table__,
            Hosted.__table__,
            Voyages.__table__,
            Subclasses.__table__,
    ):
        table.create(engine)
    return sessionmaker(bind=engine)()


def _seed(session, reference_time):
    ranks = [
        Rank(
            role_id=10, identifier="E4", name="Petty Officer", index=4, is_active=True
        ),
        Rank(
            role_id=20,
            identifier="E7",
            name="Chief Petty Officer",
            index=7,
            is_active=True,
        ),
        Rank(role_id=30, identifier="O1", name="Ensign", index=9, is_active=True),
    ]
    sailors = [
        Sailor(discord_id=1, gamertag="Host", current_rank_id=30),
        Sailor(discord_id=2, gamertag="Target", current_rank_id=20),
        Sailor(discord_id=3, gamertag="Mate", current_rank_id=20),
        Sailor(discord_id=4, gamertag="Fallback Mate", current_rank_id=10),
    ]
    session.add_all(ranks + sailors)
    session.add_all(
        [
            Hosted(
                log_id=100,
                target_id=1,
                log_time=reference_time - timedelta(hours=3),
                ship_role_id=500,
                voyage_type=VoyageType.SKIRMISH,
                gold_count=100,
                doubloon_count=10,
                fish_count=1,
                ancient_coin_count=0,
                host_rank_id=30,
                ship_name="USS Test",
            ),
            Hosted(
                log_id=101,
                target_id=2,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=600,
                voyage_type=VoyageType.PATROL,
                gold_count=50,
                doubloon_count=5,
                fish_count=0,
                ancient_coin_count=1,
                host_rank_id=None,
                ship_name="USS Other",
            ),
            Hosted(
                log_id=102,
                target_id=1,
                log_time=reference_time - timedelta(days=120),
                ship_role_id=500,
                voyage_type=VoyageType.ADVENTURE,
                gold_count=20,
                doubloon_count=2,
                host_rank_id=30,
                ship_name="USS Test",
            ),
        ]
    )
    session.add_all(
        [
            Voyages(
                log_id=100,
                target_id=2,
                log_time=reference_time - timedelta(hours=3),
                ship_role_id=500,
                participant_rank_id=20,
            ),
            Voyages(
                log_id=100,
                target_id=3,
                log_time=reference_time - timedelta(hours=3),
                ship_role_id=500,
                participant_rank_id=20,
            ),
            Voyages(
                log_id=100,
                target_id=4,
                log_time=reference_time - timedelta(hours=3),
                ship_role_id=500,
                participant_rank_id=None,
            ),
            Voyages(
                log_id=101,
                target_id=2,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=600,
                participant_rank_id=20,
            ),
            Voyages(
                log_id=101,
                target_id=4,
                log_time=reference_time - timedelta(days=2),
                ship_role_id=600,
                participant_rank_id=None,
            ),
            Voyages(
                log_id=102,
                target_id=2,
                log_time=reference_time - timedelta(days=120),
                ship_role_id=500,
                participant_rank_id=20,
            ),
        ]
    )
    session.add_all(
        [
            Subclasses(
                author_id=1,
                log_id=100,
                target_id=2,
                subclass=SubclassType.HELM,
                subclass_count=2,
                log_time=reference_time - timedelta(hours=3),
            ),
            Subclasses(
                author_id=1,
                log_id=101,
                target_id=4,
                subclass=SubclassType.CARPENTER,
                subclass_count=1,
                log_time=reference_time - timedelta(days=2),
            ),
        ]
    )
    session.commit()


def test_resolve_time_range_scales_bucket_resolution():
    reference_time = datetime(2026, 6, 12, 12, 0)

    one_hour = resolve_time_range("1h", reference_time)
    year = resolve_time_range("365d", reference_time)
    two_years = resolve_time_range("730d", reference_time)
    five_years = resolve_time_range("1825d", reference_time)
    all_time = resolve_time_range("all", reference_time)

    assert one_hour.bucket == "5min"
    assert len(one_hour.buckets) == 13
    assert year.bucket == "month"
    assert len(year.buckets) <= 13
    assert two_years.bucket == "month"
    assert five_years.bucket == "month"
    assert all_time.label == "all"
    assert all_time.start is None
    assert all_time.bucket == "month"


def test_bucket_start_for_month_uses_calendar_month():
    assert bucket_start_for(datetime(2026, 6, 12, 12, 30), "month") == datetime(
        2026, 6, 1
    )


def test_overview_filters_by_ship_user_and_voyage_type():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    analytics_range = TimeRange.from_reference("7d", reference_time)

    summary = VoyageAnalyticsService(session).build_overview(
        AnalyticsFilters(
            time_range=analytics_range,
            ship_role_id=500,
            user_id=2,
            voyage_type=VoyageType.SKIRMISH,
        )
    )

    assert summary.total_voyages == 1
    assert summary.total_hosted == 0
    assert summary.unique_sailors == 1
    assert summary.total_gold == 100
    assert summary.subclass_points[SubclassType.HELM] == 2
    assert sum(bucket.voyages for bucket in summary.bucket_series) == 1


def test_overview_all_time_includes_rows_older_than_five_years():
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
                voyage_type=VoyageType.PATROL,
                gold_count=7,
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

    summary = VoyageAnalyticsService(session).build_overview(
        AnalyticsFilters(time_range=TimeRange.from_reference("all", reference_time))
    )

    assert summary.total_voyages == 7
    assert summary.total_hosted == 4
    assert summary.total_gold == 177
    assert summary.bucket_series[0].start == datetime(old_time.year, old_time.month, 1)


def test_rank_share_prefers_voyage_rank_and_tracks_current_rank_fallback():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    rank_share = VoyageAnalyticsService(session).build_rank_share(
        AnalyticsFilters(time_range=TimeRange.from_reference("7d", reference_time))
    )

    assert rank_share.rank_counts["Chief Petty Officer"] == 3
    assert rank_share.rank_counts["Petty Officer"] == 2
    assert rank_share.fallback_count == 2


def test_user_filter_includes_logs_hosted_by_user_even_when_not_participant():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    summary = VoyageAnalyticsService(session).build_overview(
        AnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            user_id=1,
        )
    )

    assert summary.total_hosted == 1
    assert summary.total_gold == 100


def test_companion_share_preserves_voyage_drilldown_insights():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    companion_share = VoyageAnalyticsService(session).build_companion_share(
        AnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            user_id=2,
        )
    )

    assert companion_share.companion_counts == [(4, 2), (3, 1)]
    assert companion_share.shared_voyage_count == 2
    assert companion_share.companion_rank_counts["Petty Officer"] == 2
    assert companion_share.companion_rank_counts["Chief Petty Officer"] == 1
    assert companion_share.fallback_rank_count == 2
