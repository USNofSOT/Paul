import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import asc, desc, func, select, union_all

from src.config.cache import FIVE_MINUTES_IN_SECONDS
from src.data.models import Hosted, Voyages
from src.data.repository.common.base_repository import BaseRepository, Session
from src.utils.cache_utils import ttl_cache

log = logging.getLogger(__name__)


@ttl_cache(seconds=FIVE_MINUTES_IN_SECONDS, cache_name="streak_activity_dates")
def _get_voyage_activity_dates(discord_id: int) -> list[date]:
    """Internal cached helper for voyage activity dates."""
    try:
        with Session() as session:
            # Union of dates from Voyages and Hosted
            v_stmt = select(func.date(Voyages.log_time).label("d")).where(Voyages.target_id == discord_id)
            h_stmt = select(func.date(Hosted.log_time).label("d")).where(Hosted.target_id == discord_id)
            combined = union_all(v_stmt, h_stmt).subquery()

            stmt = select(func.distinct(combined.c.d).label("activity_date")).order_by(desc("activity_date"))

            rows = session.execute(stmt).fetchall()
            return [row.activity_date for row in rows]
    except Exception as e:
        log.error("Error fetching combined voyage activity dates for user %s: %s", discord_id, e)
        raise


@ttl_cache(seconds=FIVE_MINUTES_IN_SECONDS, cache_name="streak_activity_dates")
def _get_hosted_activity_dates(discord_id: int) -> list[date]:
    """Internal cached helper for hosting activity dates."""
    try:
        with Session() as session:
            stmt = (
                select(func.distinct(func.date(Hosted.log_time)).label("activity_date"))
                .where(Hosted.target_id == discord_id)
                .order_by(desc("activity_date"))
            )
            rows = session.execute(stmt).fetchall()
            return [row.activity_date for row in rows]
    except Exception as e:
        log.error("Error fetching hosted activity dates for user %s: %s", discord_id, e)
        raise


class StreakRepository(BaseRepository[Voyages]):
    """
    Repository for managing user activity streaks for voyages and hosting.
    Inherits from BaseRepository for standard session management.
    """

    def __init__(self):
        # We use Voyages as the base entity, but this repo handles multiple tables.
        super().__init__(Voyages)

    def get_voyage_activity_dates(self, discord_id: int) -> list[date]:
        """
        Returns distinct UTC calendar days with voyage activity (participated OR hosted).
        Sorted descending.
        """
        return _get_voyage_activity_dates(discord_id)

    def get_hosted_activity_dates(self, discord_id: int) -> list[date]:
        """Returns distinct UTC calendar days with hosting activity, sorted descending."""
        return _get_hosted_activity_dates(discord_id)

    def get_top_voyage_streaks(
            self,
            member_ids: list[int],
            limit: int,
            today: date | None = None,
    ) -> list[tuple[int, int]]:
        """
        Returns (target_id, streak_length) for top active voyage streaks.
        Includes both participating AND hosting activity.
        """
        v_sub = select(Voyages.target_id, Voyages.log_time).where(Voyages.target_id.in_(member_ids))
        h_sub = select(Hosted.target_id, Hosted.log_time).where(Hosted.target_id.in_(member_ids))
        combined_stmt = union_all(v_sub, h_sub).subquery()

        return self._get_top_streaks_internal(member_ids, combined_stmt, limit, active_only=True, today=today)

    def get_top_hosted_streaks(
            self,
            member_ids: list[int],
            limit: int,
            today: date | None = None,
    ) -> list[tuple[int, int]]:
        """Returns (target_id, streak_length) for top active hosting streaks."""
        hosted_stmt = select(Hosted.target_id, Hosted.log_time).where(Hosted.target_id.in_(member_ids)).subquery()
        return self._get_top_streaks_internal(member_ids, hosted_stmt, limit, active_only=True, today=today)

    def get_top_voyage_streaks_all_time(
            self,
            member_ids: list[int],
            limit: int,
    ) -> list[tuple[int, int]]:
        """Returns (target_id, streak_length) for highest historical voyage streaks."""
        v_sub = select(Voyages.target_id, Voyages.log_time).where(Voyages.target_id.in_(member_ids))
        h_sub = select(Hosted.target_id, Hosted.log_time).where(Hosted.target_id.in_(member_ids))
        combined_stmt = union_all(v_sub, h_sub).subquery()

        return self._get_top_streaks_internal(member_ids, combined_stmt, limit, active_only=False)

    def get_top_hosted_streaks_all_time(
            self,
            member_ids: list[int],
            limit: int,
    ) -> list[tuple[int, int]]:
        """Returns (target_id, streak_length) for highest historical hosting streaks."""
        hosted_stmt = select(Hosted.target_id, Hosted.log_time).where(Hosted.target_id.in_(member_ids)).subquery()
        return self._get_top_streaks_internal(member_ids, hosted_stmt, limit, active_only=False)

    def _get_top_streaks_internal(
            self,
            member_ids: list[int],
            activity_source: any,
            limit: int,
            active_only: bool,
            today: date | None = None,
    ) -> list[tuple[int, int]]:
        if not member_ids:
            return []

        actual_today = today or datetime.now(timezone.utc).date()
        yesterday = actual_today - timedelta(days=1)

        try:
            daily_activity = (
                select(
                    activity_source.c.target_id,
                    func.date(activity_source.c.log_time).label("activity_date"),
                )
                .group_by(activity_source.c.target_id, func.date(activity_source.c.log_time))
                .cte("daily_activity")
            )

            ranked = select(
                daily_activity.c.target_id,
                daily_activity.c.activity_date,
                func.row_number()
                .over(
                    partition_by=daily_activity.c.target_id,
                    order_by=asc(daily_activity.c.activity_date),
                )
                .label("rn"),
            ).cte("ranked")

            streak_groups = select(
                ranked.c.target_id,
                ranked.c.activity_date,
                func.adddate(
                    ranked.c.activity_date, -ranked.c.rn
                ).label("streak_anchor"),
            ).cte("streak_groups")

            streak_lengths = (
                select(
                    streak_groups.c.target_id,
                    streak_groups.c.streak_anchor,
                    func.count().label("streak_length"),
                    func.max(streak_groups.c.activity_date).label("most_recent_day"),
                )
                .group_by(streak_groups.c.target_id, streak_groups.c.streak_anchor)
                .cte("streak_lengths")
            )

            # Define core select
            if active_only:
                final_source = (
                    select(streak_lengths.c.target_id, streak_lengths.c.streak_length)
                    .where(streak_lengths.c.most_recent_day >= yesterday)
                    .where(streak_lengths.c.streak_length >= 2)
                )
            else:
                # All time highest per user
                user_best = select(
                    streak_lengths.c.target_id,
                    func.max(streak_lengths.c.streak_length).label("streak_length")
                ).group_by(streak_lengths.c.target_id).cte("user_best")

                final_source = (
                    select(user_best.c.target_id, user_best.c.streak_length)
                    .where(user_best.c.streak_length >= 2)
                )

            stmt = final_source.order_by(desc("streak_length")).limit(limit)

            rows = self.session.execute(stmt).fetchall()
            return [(row.target_id, row.streak_length) for row in rows]
        except Exception as e:
            log.error("Error fetching top streaks: %s", e, extra={"notify_engineer": True})
            raise
