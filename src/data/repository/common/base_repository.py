import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy.orm import Session, sessionmaker

from src.data.engine import engine

Session: sessionmaker[Session] = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, entity_type: Type[T]):
        self.session = None
        self.entity_type: Type[T] = entity_type
        self.setup()

    def setup(self) -> None:
        logger.debug("Setting up the repository for %s", self.entity_type.__name__)
        self.session = Session()

    def teardown(self) -> None:
        logger.debug("Tearing down the repository for %s", self.entity_type.__name__)
        self.close_session()

    def get_session(self):
        if self.session is None:
            logger.error(
                "Session is not set up for repository of type %s",
                self.entity_type.__name__,
            )
            raise Exception(
                "Session is not set up for repository of type %s",
                self.entity_type.__name__,
            )
        return self.session

    def close_session(self):
        self.session.close()

    def find(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[T]:
        """
        Find entities in the database by filters

        Args:
            filters: The filters to apply to the query
            limit: The maximum number of entities to return
            skip: The number of entities to skip
        Returns:
            The entities that match the filters
        Raises:
            Exception: If there is an error finding the entities
        """
        try:
            query = self.session.query(self.entity_type)
            if filters:
                query = query.filter_by(**filters)
            if limit:
                query = query.limit(limit)
            if skip:
                query = query.offset(skip)
            result = query.all()
            logger.debug(
                "Found %d entities of type %s with filters %s",
                len(result),
                self.entity_type.__name__,
                filters,
            )
            return result
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error finding entities of type %s: %s", self.entity_type.__name__, e
            )
            raise e

    def get(self, entity_id: Any) -> Optional[T]:
        """
        Get an entity from the database by ID

        Args:
            entity_id: The ID of the entity to get
        Returns:
            The entity with the given ID, or None if it does not exist
        Raises:
            Exception: If there is an error getting the entity
        """
        try:
            entity = self.session.query(self.entity_type).get(entity_id)
            logger.debug(
                "Got entity of type %s with ID %s", self.entity_type.__name__, entity_id
            )
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error getting entity of type %s with ID %s: %s",
                self.entity_type.__name__,
                entity_id,
                e,
            )
            raise e

    def create(self, entities: Union[T, List[T]]) -> Union[T, List[T]]:
        """
        Create an entity in the database

        Args:
            entities: The entity or entities to create
        Returns:
            The created entity or entities
        Raises:
            TypeError: If the entity is not the same type as the repository
            Exception: If there is an error creating the entity
        """
        if isinstance(entities, list):
            return self._create_multiple(entities)
        else:
            return self._create_single(entities)

    def update(self, entities: Union[T, List[T]]) -> Union[T, List[T]]:
        if isinstance(entities, list):
            return self._update_multiple(entities)
        else:
            return self._update_single(entities)

    def remove(self, entity: T) -> T:
        """
        Remove an entity from the database

        Args:
            entity: The entity to remove
        Returns:
            The removed entity
        Raises:
            TypeError: If the entity is not the same type as the repository
            Exception: If there is an error removing the entity
        """
        try:
            if not isinstance(entity, self.entity_type):
                raise TypeError("Entity is not the same type as the repository")
            self.session.delete(entity)
            self.session.commit()
            logger.debug(
                "Removed entity of type %s with data %s",
                self.entity_type.__name__,
                entity,
            )
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error removing entity of type %s: %s", self.entity_type.__name__, e
            )
            raise e

    def _create_multiple(self, entities: List[T]) -> List[T]:
        if not all(isinstance(entity, self.entity_type) for entity in entities):
            raise TypeError("All entities must be of the same type as the repository")
        try:
            self.session.add_all(entities)
            self.session.commit()
            logger.debug(
                "Created %d entities of type %s",
                len(entities),
                self.entity_type.__name__,
            )
            return entities
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error creating multiple entities of type %s: %s",
                self.entity_type.__name__,
                e,
            )
            raise e

    def _create_single(self, entity: T) -> T:
        if not isinstance(entity, self.entity_type):
            raise TypeError("Entity is not the same type as the repository")
        try:
            self.session.add(entity)
            self.session.commit()
            logger.debug(
                "Created entity of type %s with data %s",
                self.entity_type.__name__,
                entity,
            )
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error creating entity of type %s: %s", self.entity_type.__name__, e
            )
            raise e

    def _update_multiple(self, entities: List[T]) -> List[T]:
        if not all(isinstance(entity, self.entity_type) for entity in entities):
            raise TypeError("All entities must be of the same type as the repository")
        try:
            for entity in entities:
                self.session.add(entity)
            self.session.commit()
            logger.debug(
                "Updated %d entities of type %s",
                len(entities),
                self.entity_type.__name__,
            )
            return entities
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error updating multiple entities of type %s: %s",
                self.entity_type.__name__,
                e,
            )
            raise e

    def _update_single(self, entity: T) -> T:
        if not isinstance(entity, self.entity_type):
            raise TypeError("Entity is not the same type as the repository")
        try:
            self.session.add(entity)
            self.session.commit()
            logger.debug(
                "Updated entity of type %s with data %s",
                self.entity_type.__name__,
                entity,
            )
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(
                "Error updating entity of type %s: %s", self.entity_type.__name__, e
            )
            raise e
