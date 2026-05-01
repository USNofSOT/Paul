import logging
from datetime import date, datetime, timedelta
from typing import Optional

from attr import dataclass
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, aliased

from src.utils.streak_utils import compute_streaks
from .engine import engine
from .models import Sailor, Voyages, Hosted, Coins

log = logging.getLogger(__name__)

Session = sessionmaker(bind=engine)


@dataclass
class Rankings:
    sailor_id: int

    carpenter_rank: int
    flex_rank: int
    cannoneer_rank: int
    helm_rank: int
    grenadier_rank: int
    surgeon_rank: int
    voyages_rank: int
    hosted_rank: int


def get_ranking(discord_id: int) -> Rankings:
    rankings = Rankings(
        sailor_id=discord_id,
        carpenter_rank=0,
        flex_rank=0,
        cannoneer_rank=0,
        helm_rank=0,
        grenadier_rank=0,
        surgeon_rank=0,
        voyages_rank=0,
        hosted_rank=0,
    )

    try:
        with Session() as session:
            rank_query = text("""
                SELECT
                    discord_id,
                    carpenter_rank,
                    flex_rank,
                    cannoneer_rank,
                    helm_rank,
                    grenadier_rank,
                    surgeon_rank,
                    voyage_rank,
                    hosted_rank
                FROM (
                    SELECT
                        discord_id,
                        RANK() OVER (ORDER BY carpenter_points DESC) AS carpenter_rank,
                        RANK() OVER (ORDER BY flex_points DESC) AS flex_rank,
                        RANK() OVER (ORDER BY cannoneer_points DESC) AS cannoneer_rank,
                        RANK() OVER (ORDER BY helm_points DESC) AS helm_rank,
                        RANK() OVER (ORDER BY grenadier_points DESC) AS grenadier_rank,
                        RANK() OVER (ORDER BY surgeon_points DESC) AS surgeon_rank,
                        RANK() OVER (ORDER BY voyage_count DESC) AS voyage_rank,
                        RANK() OVER (ORDER BY hosted_count DESC) AS hosted_rank
                    FROM
                        sailor
                ) AS RankedSailor
                WHERE
                    discord_id = :discord_id
            """)

            results = session.execute(rank_query, {"discord_id": discord_id}).fetchone()
            if results:
                rankings = Rankings(*results)

    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")

    return rankings


@dataclass
class TopVoyagedTogether:
    sailor_id: int
    voyages_together: int


def top_voyaged_together(
        discord_id: int, within_id_list: list[int] = None
) -> list[TopVoyagedTogether]:
    top = []

    try:
        with Session() as session:
            me = aliased(Voyages)
            other = aliased(Voyages)

            query = (
                session.query(other.target_id, func.count().label("voyage_count"))
                .select_from(me)
                .join(other, me.log_id == other.log_id)
                .filter(me.target_id == discord_id)
                .filter(other.target_id != me.target_id)
            )

            if within_id_list:
                query = query.filter(other.target_id.in_(within_id_list))

            query = (
                query.group_by(other.target_id)
                .order_by(func.count().desc())
                .limit(3)
            )

            top = [
                TopVoyagedTogether(other_id, voyage_count)
                for other_id, voyage_count in query.all()
            ]

    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")

    return top


class MemberReport:
    sailor: Sailor

    last_voyage: Optional[datetime]
    average_weekly_voyages: float = 0.0
    voyage_streak: int = 0
    longest_voyage_streak: int = 0
    longest_voyage_start: Optional[date] = None
    longest_voyage_end: Optional[date] = None

    last_hosted: Optional[datetime]
    average_weekly_hosted: float = 0.0
    hosted_streak: int = 0
    longest_hosted_streak: int = 0
    longest_hosted_start: Optional[date] = None
    longest_hosted_end: Optional[date] = None

    coins: list[Coins]


def member_report(discord_id: int) -> MemberReport:
    session = Session()

    # Calculate the 30-day interval
    thirty_days_ago = datetime.now() - timedelta(days=30)

    try:
        # 1. Get the sailor and their last voyage and last hosted
        query = session.query(
            Sailor,
            session.query(func.max(Voyages.log_time))
            .filter(Voyages.target_id == Sailor.discord_id)
            .label("last_voyage"),
            session.query(func.count())
            .filter(
                Voyages.log_time >= thirty_days_ago,
                Voyages.target_id == Sailor.discord_id,
            )
            .label("total_voyages_in_period"),
            session.query(func.max(Hosted.log_time))
            .filter(Hosted.target_id == Sailor.discord_id)
            .label("last_hosted"),
            session.query(func.count())
            .filter(
                Hosted.log_time >= thirty_days_ago,
                Hosted.target_id == Sailor.discord_id,
            )
            .label("total_hosted_in_period"),
        ).filter(Sailor.discord_id == discord_id)

        # 2. Get the coins
        coins = session.query(Coins).filter(Coins.target_id == discord_id).all()

        # 3. Get activity dates for streaks (Optimized: fetching only what's needed for current streak)
        # Note: We fetch from repository to leverage cross-instance caching
        from src.data.repository.streak_repository import StreakRepository

        with StreakRepository() as streak_repo:
            v_dates = streak_repo.get_voyage_activity_dates(discord_id)
            h_dates = streak_repo.get_hosted_activity_dates(discord_id)

        v_curr, v_long, v_start, v_end, _ = compute_streaks(v_dates)
        h_curr, h_long, h_start, h_end, _ = compute_streaks(h_dates)

        # 4. Map the results to the MemberReport object
        report = MemberReport()

        sailor, last_voyage, total_v_period, last_hosted, total_h_period = query.one()
        report.sailor = sailor
        report.last_voyage = last_voyage
        report.average_weekly_voyages = round(total_v_period / 4.0, 2)
        report.voyage_streak = v_curr
        report.longest_voyage_streak = v_long
        report.longest_voyage_start = v_start
        report.longest_voyage_end = v_end

        report.last_hosted = last_hosted
        report.average_weekly_hosted = round(total_h_period / 4.0, 2)
        report.hosted_streak = h_curr
        report.longest_hosted_streak = h_long
        report.longest_hosted_start = h_start
        report.longest_hosted_end = h_end

        report.coins = coins

        return report

    except Exception as e:
        log.error(e)
        session.rollback()
        raise e
    finally:
        session.close()


@dataclass
class grab_top_list:
    sailor_id: int
    count: int
