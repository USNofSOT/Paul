from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from src.data import BotInteractionLog, HealthSnapshot
from src.data.repository.common.base_repository import BaseRepository

log = logging.getLogger(__name__)


class HealthSnapshotRepository(BaseRepository[HealthSnapshot]):
    def __init__(self):
        super().__init__(HealthSnapshot)

    def get_latency_window(self, minutes: int) -> tuple[float | None, float | None]:
        from sqlalchemy import func
        cutoff = datetime.now(tz=timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes)
        row = (
            self.session.query(
                func.avg(BotInteractionLog.execution_time_ms),
                func.max(BotInteractionLog.execution_time_ms),
            )
            .filter(
                BotInteractionLog.log_time >= cutoff,
                BotInteractionLog.execution_time_ms.isnot(None),
            )
            .first()
        )
        if not row or row[0] is None:
            return None, None
        return float(row[0]), float(row[1])

    def insert_snapshot(self, snapshot: HealthSnapshot) -> None:
        self.session.add(snapshot)
        self.session.commit()

    def get_latest(self) -> HealthSnapshot | None:
        return (
            self.session.query(HealthSnapshot)
            .order_by(HealthSnapshot.timestamp.desc())
            .first()
        )

    def get_avg_max_latency(self, hours: int) -> tuple[float | None, float | None]:
        row = (
            self.session.execute(
                text(
                    "SELECT AVG(execution_time_ms) AS avg_ms, MAX(execution_time_ms) AS max_ms "
                    "FROM log_bot_interaction "
                    "WHERE log_time >= NOW() - INTERVAL :h HOUR "
                    "AND execution_time_ms IS NOT NULL"
                ),
                {"h": hours},
            )
            .mappings()
            .first()
        )
        if not row:
            return None, None
        return row["avg_ms"], row["max_ms"]

    def get_recent_snapshots(self, hours: int) -> list[HealthSnapshot]:
        cutoff = datetime.now(tz=timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        return (
            self.session.query(HealthSnapshot)
            .filter(HealthSnapshot.timestamp >= cutoff)
            .order_by(HealthSnapshot.timestamp.asc())
            .all()
        )
