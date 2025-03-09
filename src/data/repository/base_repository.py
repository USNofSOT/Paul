import logging
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session, sessionmaker

from src.data.engine import engine

Session: sessionmaker[Session] = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, entity_type: Type[object]):
        self.session = Session()
        self.entity_type: Type[object] = entity_type

    def get_session(self) -> Session:
        return self.session

    def close_session(self) -> None:
        self.session.close()

    def create(self, entity: object) -> object:
        """
        Create a new entity in the database.

        Args:
            entity (object): The entity to create in the database.

        Returns:
            object: The created entity.

        Raises:
            Exception: If there is an error creating the entity.
        """
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error("Error creating entity: %s", e)
            raise e

    def find(
        self,
        entity: Type[object],
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Any]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[object]:
        """
        Find entities in the database.

        Args:
            entity (Type[object]): The entity class to find in the database.
            filters (Optional[Dict[str, Any]]): A dictionary of filters to apply to the query.
            order_by (Optional[List[Any]]): A list of columns to order the results by.
            limit (Optional[int]): The maximum number of results to return.
            skip (Optional[int]): The number of results to skip.

        Returns:
            List[object]: The found entities.

        Raises:
            Exception: If there is an error finding the entities.
        """
        try:
            query = self.session.query(entity)
            if filters:
                query = query.filter_by(**filters)
            if order_by:
                query = query.order_by(*order_by)
            if limit:
                query = query.limit(limit)
            if skip:
                query = query.offset(skip)
            return query.all()
        except Exception as e:
            self.session.rollback()
            logger.error("Error finding entities: %s", e)
            raise e

    def get(self, entity: Type[object], entity_id: Any) -> Optional[object]:
        """
        Get an entity by its ID.

        Args:
            entity (Type[object]): The entity class to get from the database.
            entity_id (Any): The ID of the entity to retrieve.

        Returns:
            Optional[object]: The found entity or None if not found.

        Raises:
            Exception: If there is an error getting the entity.
        """
        try:
            return self.session.query(entity).get(entity_id)
        except Exception as e:
            self.session.rollback()
            logger.error("Error getting entity: %s", e)
            raise e

    def update(self, entity: object) -> object:
        """
        Update an entity in the database.

        Args:
            entity (object): The entity to update in the database.

        Returns:
            object: The updated entity.

        Raises:
            Exception: If there is an error updating the entity.
        """
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error("Error updating entity: %s", e)

    def delete(self, entity: object) -> None:
        """
        Delete an entity from the database.

        Args:
            entity (object): The entity to delete from the database.

        Raises:
            Exception: If there is an error deleting the entity.
        """
        try:
            self.session.delete(entity)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error("Error deleting entity: %s", e)
            raise e

    def count(self, entity: Type[object], filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count the number of entities in the database.

        Args:
            entity (Type[object]): The entity class to count in the database.
            filters (Optional[Dict[str, Any]]): A dictionary of filters to apply to the query.

        Returns:
            int: The number of entities.

        Raises:
            Exception: If there is an error counting the entities.
        """
        try:
            query = self.session.query(entity)
            if filters:
                query = query.filter_by(**filters)
            return query.count()
        except Exception as e:
            self.session.rollback()
            logger.error("Error counting entities: %s", e)
            raise e

    def refresh(self, entity: object) -> None:
        """
        Refresh the state of an entity from the database.

        Args:
            entity (object): The entity to refresh.

        Raises:
            Exception: If there is an error refreshing the entity.
        """
        try:
            self.session.refresh(entity)
        except Exception as e:
            self.session.rollback()
            logger.error("Error refreshing entity: %s", e)
            raise e
