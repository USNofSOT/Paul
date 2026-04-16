import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func, update
from sqlalchemy.sql.functions import coalesce

from src.data import SubclassType
from src.data.models import Hosted, Sailor, Voyages
from src.data.repository.common.base_repository import BaseRepository, Session

log = logging.getLogger(__name__)


class SailorRepository(BaseRepository[Sailor]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Sailor, session)

    def get_sailor(self, target_id: int) -> Sailor | None:
        """
        Get a Sailor from the database by ID
        """
        return self.get(target_id)

    def get_or_create_sailor(self, target_id: int) -> Sailor | None:
        """
        Ensure a Sailor exists, creating one if needed.
        """
        try:
            self.session.merge(Sailor(discord_id=target_id))
            self.session.commit()
            return self.get(target_id)
        except Exception as e:
            log.error(f"Error ensuring sailor exists: {e}")
            self.session.rollback()
            return None

    def check_discord_id_exists(self, target_id: int) -> bool:
        """
        Check if a Sailor with a specific discord ID exists
        """
        try:
            exists = (
                    self.session.query(Sailor.discord_id)
                    .filter(Sailor.discord_id == target_id)
                    .scalar()
                    is not None
            )
            return exists
        except Exception as e:
            log.error(f"Error checking if discord ID exists: {e}")
            return False

    def increment_subclass_count_by_discord_id(
            self, target_id: int, subclass: SubclassType, increment: int = 1
    ) -> bool:
        column = subclass.value.lower() + "_points"
        return self._increment_column_by_discord_id(target_id, column, increment)

    def increment_force_subclass_by_discord_id(
            self, target_id: int, subclass: SubclassType, increment: int = 1
    ) -> bool:
        column = "force_" + subclass.value.lower() + "_points"
        return self._increment_column_by_discord_id(target_id, column, increment)

    def increment_force_voyage_by_discord_id(
            self, target_id: int, increment: int = 1
    ) -> bool:
        return self._increment_column_by_discord_id(
            target_id, "force_voyage_count", increment
        )

    def increment_force_hosted_by_discord_id(
            self, target_id: int, increment: int = 1
    ) -> bool:
        return self._increment_column_by_discord_id(
            target_id, "force_hosted_count", increment
        )

    def _increment_column_by_discord_id(
            self, target_id: int, column: str, increment: int
    ) -> bool:
        try:
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values({column: coalesce(getattr(Sailor, column), 0) + increment})
            )
            self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error incrementing {column}: {e}")
            self.session.rollback()
            raise e

    def update_or_create_sailor_by_discord_id(
            self, target_id: int, gamertag: str | None = None, timezone: str | None = None
    ) -> Sailor | None:
        try:
            sailor = Sailor(discord_id=target_id)
            if gamertag:
                sailor.gamertag = gamertag
            if timezone:
                sailor.timezone = timezone

            self.session.merge(sailor)
            self.session.commit()
            return self.get(target_id)
        except Exception as e:
            log.error(f"Error updating or creating sailor: {e}")
            self.session.rollback()
            raise e

    def increment_voyage_count_by_discord_id(self, target_id: int) -> bool:
        try:
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values({"voyage_count": coalesce(Sailor.voyage_count, 0) + 1})
            )
            self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error incrementing voyage count: {e}")
            self.session.rollback()
            return False

    def set_last_voyage_at_if_newer(self, target_id: int, activity_at: datetime) -> bool:
        try:
            sailor = self.get(target_id)
            if sailor is None:
                return False
            if sailor.last_voyage_at is None or sailor.last_voyage_at < activity_at:
                sailor.last_voyage_at = activity_at
                self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error setting last voyage time: {e}")
            self.session.rollback()
            return False

    def set_last_hosting_at_if_newer(self, target_id: int, activity_at: datetime) -> bool:
        try:
            sailor = self.get(target_id)
            if sailor is None:
                return False
            if sailor.last_hosting_at is None or sailor.last_hosting_at < activity_at:
                sailor.last_hosting_at = activity_at
                self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error setting last hosting time: {e}")
            self.session.rollback()
            return False

    def refresh_last_voyage_at_by_discord_id(self, target_id: int) -> datetime | None:
        try:
            latest_voyage = (
                self.session.query(func.max(Voyages.log_time))
                .filter(Voyages.target_id == target_id)
                .scalar()
            )
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values({"last_voyage_at": latest_voyage})
            )
            self.session.commit()
            return latest_voyage
        except Exception as e:
            log.error(f"Error refreshing last voyage time: {e}")
            self.session.rollback()
            raise e

    def refresh_last_hosting_at_by_discord_id(self, target_id: int) -> datetime | None:
        try:
            latest_hosting = (
                self.session.query(func.max(Hosted.log_time))
                .filter(Hosted.target_id == target_id)
                .scalar()
            )
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values({"last_hosting_at": latest_hosting})
            )
            self.session.commit()
            return latest_hosting
        except Exception as e:
            log.error(f"Error refreshing last hosting time: {e}")
            self.session.rollback()
            raise e

    def get_sailors_with_activity(self, activity_field: str) -> list[Sailor]:
        try:
            activity_column = getattr(Sailor, activity_field)
            return self.session.query(Sailor).filter(activity_column.isnot(None)).all()
        except Exception as e:
            log.error(
                f"Error retrieving sailors with activity field {activity_field}: {e}"
            )
            raise e

    def get_sailors_with_any_activity(self, activity_fields: list[str]) -> list[Sailor]:
        try:
            filters = [getattr(Sailor, field).isnot(None) for field in activity_fields]
            from sqlalchemy import or_

            return self.session.query(Sailor).filter(or_(*filters)).all()
        except Exception as e:
            log.error(
                f"Error retrieving sailors with any activity fields {activity_fields}: {e}"
            )
            raise e

    def decrement_subclass_count_by_discord_id(
            self, target_id: int, subclass: SubclassType, subclass_count: int
    ) -> bool:
        column = subclass.value.lower() + "_points"
        try:
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values(
                    {
                        column: func.greatest(
                            coalesce(getattr(Sailor, column), 0) - subclass_count, 0
                        )
                    }
                )
            )
            self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error decrementing subclass count: {e}")
            self.session.rollback()
            return False

    def get_top_members_by_subclass(
            self, subclass_name: str, limit: int, member_list: list[int]
    ):
        if limit is None:
            limit = 3
        try:
            subclass_col = subclass_name + "_points"
            return (
                self.session.query(Sailor.discord_id, getattr(Sailor, subclass_col))
                .filter(Sailor.discord_id.in_(member_list))
                .order_by(desc(getattr(Sailor, subclass_col)))
                .limit(limit)
                .all()
            )
        except Exception as e:
            log.error(f"Error getting top members by subclass '{subclass_name}': {e}")
            return []

    def get_top_members_by_hosting_count(self, limit: int, member_list: list[int]):
        if limit is None:
            limit = 3
        try:
            return (
                self.session.query(Sailor.discord_id, Sailor.hosted_count)
                .filter(Sailor.discord_id.in_(member_list))
                .order_by(desc(Sailor.hosted_count))
                .limit(limit)
                .all()
            )
        except Exception as e:
            log.error(f"Error getting top members by hosting count: {e}")
            return []

    def get_top_members_by_voyage_count(self, limit: int, member_list: list[int]):
        if limit is None:
            limit = 3
        try:
            return (
                self.session.query(Sailor.discord_id, Sailor.voyage_count)
                .filter(Sailor.discord_id.in_(member_list))
                .order_by(desc(Sailor.voyage_count))
                .limit(limit)
                .all()
            )
        except Exception as e:
            log.error(f"Error getting top members by voyage count: {e}")
            return []


def ensure_sailor_exists(target_id: int) -> Sailor | None:
    with SailorRepository() as repo:
        try:
            sailor = Sailor(discord_id=target_id)
            repo.session.merge(sailor)
            repo.session.commit()
            return repo.get(target_id)
        except Exception as e:
            log.error(f"Error ensuring sailor exists: {e}")
            return None


def save_sailor(target_id: int) -> bool:
    with SailorRepository() as repo:
        try:
            repo.session.add(Sailor(discord_id=target_id))
            repo.session.commit()
            return True
        except Exception as e:
            log.error(f"Error adding sailor: {e}")
            repo.session.rollback()
            raise e


def get_gamertag_by_discord_id(target_id: int) -> str | None:
    with SailorRepository() as repo:
        sailor = repo.get(target_id)
        return sailor.gamertag if sailor else None


def get_timezone_by_discord_id(target_id: int) -> str | None:
    with SailorRepository() as repo:
        sailor = repo.get(target_id)
        return sailor.timezone if sailor else None


def decrement_hosted_count_by_discord_id(target_id: int) -> bool:
    with SailorRepository() as repo:
        try:
            repo.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values(
                    {
                        "hosted_count": func.greatest(
                            func.coalesce(Sailor.hosted_count, 0) - 1, 0
                        )
                    }
                )
            )
            repo.session.commit()
            return True
        except Exception as e:
            log.error(f"Error decrementing hosted count: {e}")
            repo.session.rollback()
            raise e


def decrement_voyage_count_by_discord_id(target_id: int) -> bool:
    with SailorRepository() as repo:
        try:
            repo.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values(
                    {
                        "voyage_count": func.greatest(
                            func.coalesce(Sailor.voyage_count, 0) - 1, 0
                        )
                    }
                )
            )
            repo.session.commit()
            return True
        except Exception as e:
            log.error(f"Error decrementing voyage count: {e}")
            repo.session.rollback()
            raise e
