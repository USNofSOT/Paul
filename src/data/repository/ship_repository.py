import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data import engine, ShipSize
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class ShipRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def get_most_recent_ship_size(self, ship_role_id: int) -> Type[ShipSize] | None:
        try:
            return self.session.query(ShipSize).filter(ShipSize.ship_role_id == ship_role_id).order_by(ShipSize.log_time.desc()).first()
        except Exception as e:
            log.error(f"Error getting most recent ship size: {e}")
            raise e

    def save_ship_size(self, ship_role_id: int, size: int) -> ShipSize:
        try:
            ship_size = ShipSize(
                ship_role_id=ship_role_id,
                member_count=size,
                log_time=utc_time_now()
            )
            self.session.add(ship_size)
            self.session.commit()
            return ship_size
        except Exception as e:
            log.error(f"Error saving ship size: {e}")
            self.session.rollback()
            raise e