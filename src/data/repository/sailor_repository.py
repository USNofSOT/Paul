import logging
from typing import Any, Type

from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce, func

from src.data import SubclassType
from src.data.engine import engine
from src.data.models import Sailor

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class SailorRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def increment_subclass_count_by_discord_id(self, target_id: int, subclass: SubclassType, increment: int = 1) -> bool:
        """
        Increment the subclass count for a specific Sailor

        Args:
            target_id (int): The Discord ID of the user.
            subclass (SubclassType): The subclass to increment the count for.
            increment (int): The amount to increment the count by.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        column = subclass.value.lower() + "_points"
        try:
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values({
                    column: coalesce(getattr(Sailor, column), 0) + increment
                })
            )
            self.session.commit()
        except Exception as e:
            log.error(f"Error incrementing subclass count: {e}")
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def update_or_create_sailor_by_discord_id(self, target_id: int, gamertag: str | None = None,
                                              timezone: str | None = None) -> Sailor | None:
        """
        Set the gamertag and or timezone for a Sailor by Discord ID
        Will create a new Sailor if one does not exist

        Args:
            target_id (int): The Discord ID of the user.
            gamertag (str | None): The gamertag to set for the user. Optional.
            timezone (str | None): The timezone to set for the user. Optional.
        Returns:
            Sailor: The Sailor object that was updated, or None if the operation failed.
        """
        try:
            sailor = Sailor(discord_id=target_id)

            # Ensures that the gamertag and timezone are only altered if they are not None
            if gamertag:
                sailor.gamertag = gamertag
            if timezone:
                sailor.timezone = timezone

            self.session.merge(sailor)  # merge will update or create the sailor object if it doesn't exist
            self.session.commit()
            return self.session.query(Sailor).filter(
                Sailor.discord_id == target_id).first()  # This will return the updated Sailor object
        except Exception as e:
            log.error(f"Error setting gamertag: {e}")
            self.session.rollback()
            raise e

    def increment_voyage_count_by_discord_id(self, target_id: int) -> bool:
        """
        Increment the voyage_count column for a specific Sailor

        Args:
            target_id (int): The Discord ID of the user.
        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            self.session.execute(
                update(Sailor)
                .where(Sailor.discord_id == target_id)
                .values({
                    "voyage_count": coalesce(Sailor.voyage_count, 0) + 1
                })
            )
            self.session.commit()
            return True
        except Exception as e:
            log.error(f"Error incrementing voyage count: {e}")
            self.session.rollback()
            return False


def ensure_sailor_exists(target_id: int) -> Type[Sailor] | None:
    """
    Ensure that a Sailor exists in the database

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        Sailor: The Sailor object that was created or retrieved.
    """
    session = Session()
    try:
        sailor = Sailor(discord_id=target_id)
        session.merge(sailor) # merge will update or create the sailor object if it doesn't exist
        session.commit()
        return session.query(Sailor).filter(Sailor.discord_id == target_id).first() # This will return the updated Sailor object
    except Exception as e:
        log.error(f"Error checking if Sailor exists: {e}")
    finally:
        session.close()

def save_sailor(target_id: int) -> bool:
    """
    Add a Sailor to the database

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.add(Sailor(discord_id=target_id))
        session.commit()
        return True
    except Exception as e:
        log.error(f"Error adding discord ID: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_gamertag_by_discord_id(target_id: int) -> str | None:
    """
    Get the gamertag of a Sailor

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        str | None: The gamertag of the user, or None if the user is not found or the gamertag is not set.
    """
    session = Session()
    try:
        sailor = session.query(Sailor).filter(Sailor.discord_id == target_id).first()
        return sailor.gamertag if sailor else None
    except Exception as e:
        log.error(f"Error retrieving gamertag: {e}")
        return None
    finally:
        session.close()

def get_timezone_by_discord_id(target_id: int) -> str | None:
    """
    Get the timezone of a Sailor

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        str | None: The timezone of the user, or None if the user is not found or the timezone is not set.
    """
    session = Session()
    try:
        sailor = session.query(Sailor).filter(Sailor.discord_id == target_id).first()
        return sailor.timezone if sailor else None
    except Exception as e:
        log.error(f"Error retrieving timezone: {e}")
        return None
    finally:
        session.close()

def decrement_hosted_count_by_discord_id(target_id: int) -> bool:
    """
    Decrement the hosted_count column for a specific Sailor.

    Cannot go below 0.

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.execute(
            update(Sailor)
            .where(Sailor.discord_id == target_id)
            .values({
                "hosted_count": func.greatest(func.coalesce(Sailor.hosted_count, 0) - 1, 0)
            })
        )
        session.commit()
        return True
    except Exception as e:
        log.error(f"Error decrementing hosted count: {e}")
        session.rollback()
        return False
    finally:
        session.close()
        

def decrement_voyage_count_by_discord_id(target_id: int) -> bool:
    """
    Decrement the voyage_count column for a specific Sailor

    Cannot go below 0

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    session = Session()
    try:
        session.execute(
            update(Sailor)
            .where(Sailor.discord_id == target_id)
            .values({
                "voyage_count": func.greatest(func.coalesce(Sailor.voyage_count, 0) - 1, 0)
            })
        )
        session.commit()
        return True
    except Exception as e:
        log.error(f"Error decrementing voyage count: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def check_discord_id_exists(target_id: int) -> bool:
    """
    Check if a Sailor with a specific discord ID exists

    Args:
        target_id (int): The Discord ID of the user.
    Returns:
        bool: True if a Sailor with the discord ID exists, False otherwise.
    """
    session = Session()
    try:
        exists = session.query(Sailor.discord_id).filter(Sailor.discord_id == target_id).scalar() is not None
        return exists
    except Exception as e:
        log.error(f"Error checking if discord ID exists: {e}")
        return False
    finally:
        session.close()
