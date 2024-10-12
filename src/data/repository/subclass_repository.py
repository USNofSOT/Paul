import datetime
import logging
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.data import SubclassType
from src.data.engine import engine
from src.data.models import Subclasses
from src.data.repository.sailor_repository import ensure_sailor_exists, increment_subclass_count_by_discord_id

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)
class SubclassRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def save_subclass(self, author_id: int, log_id: int, target_id: int, subclass: SubclassType, subclass_count: int = 1, log_time: datetime = datetime.datetime.now()) -> Subclasses or int:
        """
        Save a subclass record to the database

        Args:
            author_id (int): The Discord ID of the author
            log_id (int): The ID of the log message
            target_id (int): The Discord ID of the target user
            subclass (SubclassType): The subclass to log
            subclass_count (int): The number of times the subclass was logged
            log_time (datetime): The time the log was created
        Returns:
            Subclasses: The subclass record that was saved
            -1: If a duplicate record is found
        """

        try:
            # Check if a record with the same target_id, subclass, and log_link already exists
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
            increment_subclass_count_by_discord_id(target_id, subclass, subclass_count)
            self.session.commit()

            return new_subclass

        except Exception as e:
            log.error(f"Error saving subclass record: {e}")
            self.session.rollback()
            raise e
