from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.analytics.ping_analytics import PingAnalyticsFilters, PingAnalyticsService
from src.analytics.ranges import TimeRange
from src.data.models import RolePingLog


def _session():
    engine = create_engine("sqlite:///:memory:")
    RolePingLog.__table__.create(engine)
    return sessionmaker(bind=engine)()


def _seed(session, reference_time):
    session.add_all(
        [
            RolePingLog(
                user_id=1,
                channel_id=10,
                message_id=100,
                ping_role_id=5000,
                ping_type="VOYAGE_LFG",
                highest_rank_role_id=20,
                ship_role_id=500,
                has_vp_permission=True,
                is_deleted=False,
                created_at=reference_time - timedelta(hours=2),
            ),
            RolePingLog(
                user_id=2,
                channel_id=10,
                message_id=101,
                ping_role_id=6000,
                ping_type="VOYAGE_LFG",
                highest_rank_role_id=30,
                ship_role_id=600,
                has_vp_permission=False,
                is_deleted=False,
                created_at=reference_time - timedelta(days=2),
            ),
            RolePingLog(
                user_id=1,
                channel_id=10,
                message_id=102,
                ping_role_id=5000,
                ping_type="VOYAGE_LFG",
                highest_rank_role_id=20,
                ship_role_id=500,
                has_vp_permission=True,
                is_deleted=True,
                created_at=reference_time - timedelta(hours=1),
            ),
        ]
    )
    session.commit()


def test_ping_summary_filters_by_ping_ship_user_and_vp_status():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    summary = PingAnalyticsService(session).build_summary(
        PingAnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            ping_role_id=5000,
            ship_role_id=500,
            user_id=1,
            has_vp_permission=True,
        )
    )

    assert summary.total_pings == 1
    assert summary.vp_enabled_pings == 1
    assert summary.non_vp_pings == 0
    assert summary.rank_counts == {20: 1}
    assert sum(bucket.total for bucket in summary.bucket_series) == 1


def test_ping_summary_excludes_deleted_rows():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)

    summary = PingAnalyticsService(session).build_summary(
        PingAnalyticsFilters(
            time_range=TimeRange.from_reference("1d", reference_time),
            user_id=1,
        )
    )

    assert summary.total_pings == 1
    assert summary.deleted_rows_excluded == 1


def test_ping_summary_all_time_includes_rows_older_than_five_years():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    _seed(session, reference_time)
    old_time = reference_time - timedelta(days=2200)
    session.add(
        RolePingLog(
            user_id=3,
            channel_id=10,
            message_id=900,
            ping_role_id=5000,
            ping_type="VOYAGE_LFG",
            highest_rank_role_id=40,
            ship_role_id=700,
            has_vp_permission=False,
            is_deleted=False,
            created_at=old_time,
        )
    )
    session.commit()

    summary = PingAnalyticsService(session).build_summary(
        PingAnalyticsFilters(time_range=TimeRange.from_reference("all", reference_time))
    )

    assert summary.total_pings == 3
    assert summary.ship_counts[700] == 1
    assert summary.bucket_series[0].start == datetime(old_time.year, old_time.month, 1)
