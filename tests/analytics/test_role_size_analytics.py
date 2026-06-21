from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.analytics.ranges import TimeRange, role_size_time_range
from src.analytics.role_size_analytics import (
    RoleSizeAnalyticsFilters,
    RoleSizeAnalyticsService,
)
from src.data.models import RoleSize, RoleType


def _session():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE role_size
                (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id      BIGINT      NOT NULL,
                    role_type    VARCHAR(16) NOT NULL,
                    member_count INTEGER     NOT NULL,
                    log_time     DATETIME    NOT NULL
                )
                """
            )
        )
    return sessionmaker(bind=engine)()


def test_role_size_range_clamps_hourly_to_daily_buckets():
    reference_time = datetime(2026, 6, 12, 12, 0)

    result = role_size_time_range("1h", reference_time)

    assert result.bucket == "day"
    assert result.label == "1d"


def test_role_size_all_time_uses_month_buckets():
    reference_time = datetime(2026, 6, 12, 12, 0)

    result = role_size_time_range("all", reference_time)

    assert result.label == "all"
    assert result.start is None
    assert result.bucket == "month"


def test_role_size_summary_uses_last_snapshot_before_bucket():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    session.add_all(
        [
            RoleSize(
                role_id=500,
                role_type=RoleType.SHIP,
                member_count=10,
                log_time=reference_time - timedelta(days=3),
            ),
            RoleSize(
                role_id=500,
                role_type=RoleType.SHIP,
                member_count=12,
                log_time=reference_time - timedelta(days=1, hours=1),
            ),
        ]
    )
    session.commit()

    summary = RoleSizeAnalyticsService(session).build_summary(
        RoleSizeAnalyticsFilters(
            time_range=TimeRange.from_reference("7d", reference_time),
            role_ids=(500,),
            role_type=RoleType.SHIP,
        )
    )

    assert summary.series[500][-1].member_count == 12
    assert summary.series[500][-2].member_count == 12


def test_role_size_summary_all_time_includes_old_snapshots():
    reference_time = datetime(2026, 6, 12, 12, 0)
    session = _session()
    old_time = reference_time - timedelta(days=2200)
    session.add_all(
        [
            RoleSize(
                role_id=500,
                role_type=RoleType.RANK,
                member_count=4,
                log_time=old_time,
            ),
            RoleSize(
                role_id=500,
                role_type=RoleType.RANK,
                member_count=9,
                log_time=reference_time - timedelta(days=1),
            ),
        ]
    )
    session.commit()

    summary = RoleSizeAnalyticsService(session).build_summary(
        RoleSizeAnalyticsFilters(
            time_range=role_size_time_range("all", reference_time),
            role_ids=(500,),
            role_type=RoleType.RANK,
        )
    )

    assert summary.series[500][0].start == datetime(old_time.year, old_time.month, 1)
    assert summary.series[500][0].member_count == 4
    assert summary.series[500][-1].member_count == 9
