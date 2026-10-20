import logging
from typing import Type

from src.data.models import RoleSize, RoleType
from src.data.repository.common.base_repository import BaseRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class RoleRepository(BaseRepository[RoleSize]):
    def __init__(self):
        super().__init__(RoleSize)

    def get_role_sizes(self, role_id: int) -> list[Type[RoleSize]]:
        try:
            return self.session.query(RoleSize).filter(RoleSize.role_id == role_id).all()
        except Exception as e:
            log.error(f"Error getting role sizes: {e}")
            raise e

    def get_most_recent_role_size(self, role_id: int) -> Type[RoleSize] | None:
        try:
            return self.session.query(RoleSize).filter(RoleSize.role_id == role_id).order_by(
                RoleSize.log_time.desc()).first()
        except Exception as e:
            log.error(f"Error getting most recent role size: {e}")
            raise e

    def save_role_size(self, role_id: int, size: int, role_type: RoleType) -> RoleSize:
        try:
            role_size = RoleSize(
                role_id=role_id,
                role_type=role_type,
                member_count=size,
                log_time=utc_time_now()
            )
            self.session.add(role_size)
            self.session.commit()
            return role_size
        except Exception as e:
            log.error(f"Error saving role size: {e}")
            self.session.rollback()
            raise e
