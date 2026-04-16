import logging
import time
from functools import wraps
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy.exc import OperationalError, InternalError
from sqlalchemy.orm import Session, sessionmaker

from src.data.engine import engine

Session: sessionmaker[Session] = sessionmaker(bind=engine)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _with_transient_retry(func):
    """Decorator to retry a database operation on transient failures."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        last_exception = None
        for attempt in range(3):
            try:
                return func(self, *args, **kwargs)
            except (OperationalError, InternalError) as e:
                last_exception = e
                # Only retry on specific transient errors (like connection resets)
                # 1213: Deadlock, 1205: Lock wait timeout, 2006: MySQL server has gone away
                # 2013: Lost connection during query
                is_transient = (
                        hasattr(e, 'orig')
                        and hasattr(e.orig, 'args')
                        and e.orig.args[0] in {1213, 1205, 2006, 2013}
                )

                if not is_transient:
                    raise

                logger.warning(
                    "Transient DB error on %s (attempt %d/3): %s",
                    func.__name__, attempt + 1, e,
                    notify_engineer=True
                )
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    # If we own the session, we might need to rollback.
                    try:
                        self.session.rollback()
                    except Exception:
                        pass
        raise last_exception

    return wrapper


class BaseRepository(Generic[T]):
    def __init__(self, entity_type: Type[T], session: Optional[Session] = None):
        self.entity_type: Type[T] = entity_type
        self._owned_session = False
        self._closed = False

        if session:
            self.session = session
        else:
            self.session = Session()
            self._owned_session = True

    def __enter__(self):
        return self

    def __del__(self):
        try:
            self.close_session()
        except Exception:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()

    def close_session(self):
        if self._closed:
            return

        if self._owned_session and self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.error("Error closing session: %s", e, notify_engineer=True)

        self._closed = True
        self.session = None

    def _validate_entity_type(self, entity: Any) -> None:
        if not isinstance(entity, self.entity_type):
            raise TypeError(
                f"Entity must be of type {self.entity_type.__name__}, "
                f"got {type(entity).__name__}"
            )

    @_with_transient_retry
    def find(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[T]:
        if self._closed:
            raise RuntimeError(f"{type(self).__name__} is closed")
            
        try:
            query = self.session.query(self.entity_type)
            if filters:
                query = query.filter_by(**filters)
            if limit:
                query = query.limit(limit)
            if skip:
                query = query.offset(skip)
            return query.all()
        except Exception as e:
            if self.session:
                self.session.rollback()
            logger.error("Error finding entities of type %s: %s", self.entity_type.__name__, e, notify_engineer=True)
            raise

    @_with_transient_retry
    def get(self, entity_id: Any) -> Optional[T]:
        if self._closed:
            raise RuntimeError(f"{type(self).__name__} is closed")
            
        try:
            # SQLAlchemy 2.0 style session.get
            return self.session.get(self.entity_type, entity_id)
        except Exception as e:
            if self.session:
                self.session.rollback()
            logger.error("Error getting entity %s with ID %s: %s", self.entity_type.__name__, entity_id, e,
                         notify_engineer=True)
            raise

    @_with_transient_retry
    def create(self, entities: Union[T, List[T]]) -> Union[T, List[T]]:
        if self._closed:
            raise RuntimeError(f"{type(self).__name__} is closed")
            
        if isinstance(entities, list):
            for entity in entities:
                self._validate_entity_type(entity)
            return self._create_multiple(entities)
        else:
            self._validate_entity_type(entities)
            return self._create_single(entities)

    @_with_transient_retry
    def update(self, entities: Union[T, List[T]]) -> Union[T, List[T]]:
        if self._closed:
            raise RuntimeError(f"{type(self).__name__} is closed")
            
        if isinstance(entities, list):
            for entity in entities:
                self._validate_entity_type(entity)
            return self._update_multiple(entities)
        else:
            self._validate_entity_type(entities)
            return self._update_single(entities)

    @_with_transient_retry
    def remove(self, entity: T) -> T:
        if self._closed:
            raise RuntimeError(f"{type(self).__name__} is closed")

        self._validate_entity_type(entity)
        try:
            self.session.delete(entity)
            self.session.commit()
            return entity
        except Exception as e:
            if self.session:
                self.session.rollback()
            logger.error("Error removing entity: %s", e, notify_engineer=True)
            raise

    def _create_multiple(self, entities: List[T]) -> List[T]:
        try:
            self.session.add_all(entities)
            self.session.commit()
            return entities
        except Exception as e:
            self.session.rollback()
            logger.error("Error creating multiple entities: %s", e, notify_engineer=True)
            raise

    def _create_single(self, entity: T) -> T:
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error("Error creating entity: %s", e, notify_engineer=True)
            raise

    def _update_multiple(self, entities: List[T]) -> List[T]:
        try:
            for entity in entities:
                self.session.add(entity)
            self.session.commit()
            return entities
        except Exception as e:
            self.session.rollback()
            logger.error("Error updating multiple entities: %s", e, notify_engineer=True)
            raise

    def _update_single(self, entity: T) -> T:
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error("Error updating entity: %s", e, notify_engineer=True)
            raise
