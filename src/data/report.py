import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, aliased

log = logging.getLogger(__name__)

from .models import Sailor, Voyages, Hosted, Coins
from .engine import engine

Session = sessionmaker(bind=engine)

class MemberReport:
    sailor: Sailor

    last_voyage: datetime
    average_weekly_voyages: float = 0.0

    last_hosted: datetime
    average_weekly_hosted: float = 0.0

    coins: [Coins]


def member_report(discord_id: int) -> MemberReport:
    session = Session()

    # Calculate the 30-day interval
    thirty_days_ago = datetime.now() - timedelta(days=30)

    try:
        # 1. Get the sailor and their last voyage and last hosted
        query = (
            session.query(
                Sailor,
                session.query(func.max(Voyages.log_time)).filter(Voyages.target_id == Sailor.discord_id).label('last_voyage'),
                session.query(func.count()).filter(Voyages.log_time >= thirty_days_ago, Voyages.target_id == Sailor.discord_id).label('total_voyages_in_period'),
                session.query(func.max(Hosted.log_time)).filter(Hosted.target_id == Sailor.discord_id).label('last_hosted'),
                session.query(func.count()).filter(Hosted.log_time >= thirty_days_ago, Hosted.target_id == Sailor.discord_id).label('total_hosted_in_period')
             )
            .filter(Sailor.discord_id == discord_id)
        )

        # 2. Get the coins
        coins = session.query(Coins).filter(Coins.target_id == discord_id).all()

        # 3. Map the results to the MemberReport object
        report = MemberReport()

        sailor, last_voyage, total_voyages_in_period, last_hosted, total_hosted_in_period = query.one()
        report.sailor = sailor
        report.last_voyage = last_voyage
        report.average_weekly_voyages = round(total_voyages_in_period / 4.0, 2)
        report.last_hosted = last_hosted
        report.average_weekly_hosted = round(total_hosted_in_period / 4.0, 2)
        report.coins = coins


        return report

    except Exception as e:
        log.error(e)
        session.rollback()
    finally:
        session.close()
