import logging
from typing import Type

from src.data import ShipSize
from src.data.repository.common.base_repository import BaseRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class ShipRepository(BaseRepository[ShipSize]):
    def __init__(self):
        super().__init__(ShipSize)

    def get_ship_sizes(self, ship_role_id: int) -> list[Type[ShipSize]]:
        try:
            return self.session.query(ShipSize).filter(ShipSize.ship_role_id == ship_role_id).all()
        except Exception as e:
            log.error(f"Error getting ship sizes: {e}")
            raise e

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
