import logging
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, aliased

log = logging.getLogger(__name__)

from .models import Sailor, Voyages, Hosted, Coins
from .engine import engine

Session = sessionmaker(bind=engine)

class MemberReport:
    sailor: Sailor

    last_voyage: datetime
    average_weekly_voyages: float # TODO: Implement this

    last_hosted: datetime
    average_weekly_hosted: float # TODO: Implement this

    coins: [Coins]


def member_report(discord_id: int) -> MemberReport:
    session = Session()
    try:
        # 1. Get the sailor and their last voyage and last hosted
        query = (
            session.query(
                Sailor,
                session.query(func.max(Voyages.log_time)).filter(Voyages.target_id == Sailor.discord_id).label('last_voyage'),
                session.query(func.max(Hosted.log_time)).filter(Hosted.target_id == Sailor.discord_id).label('last_hosted')
            )
            .filter(Sailor.discord_id == discord_id)
        )

        # 2. Get the coins
        coins = session.query(Coins).filter(Coins.target_id == discord_id).all()

        # TODO: 3. Get the average weekly voyages and hosted
        # NOTE: Things to consider: over what period of time is this average calculated?

        # 4. Map the results to the MemberReport object
        report = MemberReport()
        for sailor, last_voyage, last_hosted in query:
            report.sailor = sailor
            report.last_voyage = last_voyage
            report.last_hosted = last_hosted
            report.coins = coins

        return report

    except Exception as e:
        log.error(e)
        session.rollback()
    finally:
        session.close()
