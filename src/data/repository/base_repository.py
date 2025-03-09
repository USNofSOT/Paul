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
        if not isinstance(entity, self.entity_type):
            raise TypeError("Entity is not the same type as the repository")
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
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Any]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[object]:
        try:
            query = self.session.query(self.entity_type)
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

    def get(self, entity_id: Any) -> Optional[object]:
        try:
            return self.session.query(self.entity_type).get(entity_id)
        except Exception as e:
            self.session.rollback()
            logger.error("Error getting entity: %s", e)
            raise e

    def update(self, entity: object) -> object:
        try:
            self.session.add(entity)
            self.session.commit()
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error("Error updating entity: %s", e)

    def delete(self, entity: object) -> None:
        try:
            self.session.delete(entity)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error("Error deleting entity: %s", e)
            raise e

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        try:
            query = self.session.query(self.entity_type)
            if filters:
                query = query.filter_by(**filters)
            return query.count()
        except Exception as e:
            self.session.rollback()
            logger.error("Error counting entities: %s", e)
            raise e

    def refresh(self, entity: object) -> None:
        try:
            self.session.refresh(entity)
        except Exception as e:
            self.session.rollback()
            logger.error("Error refreshing entity: %s", e)
            raise e
