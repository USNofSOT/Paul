import datetime
import logging
from typing import Optional, List

from src.data import SubclassType
from src.data.models import Subclasses
from src.data.repository.common.base_repository import BaseRepository, Session
from src.data.repository.sailor_repository import SailorRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


class SubclassRepository(BaseRepository[Subclasses]):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(Subclasses, session)
        # Shared session with SailorRepository
        self.sailor_repository = SailorRepository(session=self.session)

    def close_session(self):
        super().close_session()
        # SailorRepository shares our session; mark it closed so its guards fire correctly.
        self.sailor_repository._closed = True
        self.sailor_repository.session = None

    def entries_for_target_id(self, target_id: int, limit: int = 10) -> List[Subclasses]:
        return (
            self.session.query(Subclasses)
            .filter(Subclasses.target_id == target_id)
            .order_by(Subclasses.log_time.desc())
            .limit(limit)
            .all()
        )

    def entries_for_log_id(self, log_id: int) -> List[Subclasses]:
        """
        Retrieve all subclass entries for a specific log ID
        """
        return self.session.query(Subclasses).filter(Subclasses.log_id == log_id).all()

    def entries_for_log_id_and_target_id(self, log_id: int, target_id: int) -> List[Subclasses]:
        """
        Retrieve all subclass entries for a specific log ID and target ID
        """
        return self.session.query(Subclasses).filter(
            Subclasses.log_id == log_id,
            Subclasses.target_id == target_id
        ).all()

    def save_subclass(self, author_id: int, log_id: int, target_id: int, subclass: SubclassType,
                      subclass_count: int = 1, log_time: datetime.datetime = None) -> Subclasses:
        """
        Save a subclass record to the database
        """
        log_time = log_time or utc_time_now()
        try:
            # Check if a record with the same target_id, subclass, and log_id already exists
            existing = self.session.query(Subclasses).filter(
                Subclasses.target_id == target_id,
                Subclasses.subclass == subclass,
                Subclasses.log_id == log_id
            ).first()

            if existing:
                log.warning(f"Duplicate subclass record found for {target_id} and {subclass} under log {log_id}, skipping")
                return existing

            # Insert a new record if no duplicates are found
            new_subclass = Subclasses(
                author_id=author_id,
                log_id=log_id,
                target_id=target_id,
                subclass=subclass,
                log_time=log_time,
                subclass_count=subclass_count
            )

            self.session.add(new_subclass)
            # Increment the subclass count for the target
            self.sailor_repository.increment_subclass_count_by_discord_id(target_id, subclass, subclass_count)
            self.session.commit()

            return new_subclass

        except Exception as e:
            log.error(f"Error saving subclass record: {e}")
            self.session.rollback()
            raise e

    def delete_subclasses_for_target_in_log(self, target_id: int, log_id: int):
        """
        Clear all subclass entries for a specific target in a specific log
        """
        try:
            # Get entries for the log
            entries = self.entries_for_log_id_and_target_id(log_id, target_id)

            # Remove all subclass counts
            for entry in entries:
                self.sailor_repository.decrement_subclass_count_by_discord_id(entry.target_id, entry.subclass, entry.subclass_count)

            # Delete all entries
            self.session.query(Subclasses).filter(
                Subclasses.target_id == target_id,
                Subclasses.log_id == log_id
            ).delete()

            self.session.commit()

        except Exception as e:
            log.error(f"Error clearing subclass entries for target {target_id} in log {log_id}: {e}")
            self.session.rollback()
            raise e

    def delete_all_subclass_entries_for_log_id(self, log_id: int):
        """
        Delete all subclass entries for a specific log ID
        """
        try:
            # Get entries for the log
            entries = self.entries_for_log_id(log_id)
            # Remove all subclass counts
            for entry in entries:
                self.sailor_repository.decrement_subclass_count_by_discord_id(entry.target_id, entry.subclass, entry.subclass_count)
            # Delete all entries
            self.session.query(Subclasses).filter(Subclasses.log_id == log_id).delete()
            self.session.commit()
        except Exception as e:
            log.error(f"Error deleting subclass entries for log {log_id}: {e}")
            self.session.rollback()
            raise e
