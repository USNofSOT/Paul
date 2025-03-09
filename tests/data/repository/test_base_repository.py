import unittest

from data.repository.base_repository import BaseRepository
from parameterized import parameterized
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class EntityA(Base):
    __tablename__ = "entity_a"
    id = Column(Integer, primary_key=True)


class EntityARepository(BaseRepository):
    def __init__(self):
        super().__init__(EntityA)


class EntityB(Base):
    __tablename__ = "entity_b"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class EntityBRepository(BaseRepository):
    def __init__(self):
        super().__init__(EntityB)


class TestBaseRepository(unittest.TestCase):
    def setUp(self):
        """Set up test dependencies."""
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        self.session = self.Session()
        self.repositoryA = EntityARepository()
        self.repositoryA.session = self.session
        self.repositoryB = EntityBRepository()
        self.repositoryB.session = self.session

    def tearDown(self):
        """Tear down test dependencies."""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_create(self):
        entity = EntityA(id=6)
        self.repositoryA.create(entity)
        self.assertEqual(entity.id, 6)

    @parameterized.expand(
        [
            ("wrong_entity_for_A", EntityARepository(), EntityB()),
            ("wrong_entity_for_B", EntityBRepository(), EntityA()),
        ]
    )
    def test_create_wrong_entity_type(self, name, repository, entity):
        with self.assertRaises(TypeError):
            repository.create(entity)

    @parameterized.expand(
        [
            ("no_objects", [], 0),
            ("one_object", [EntityA(id=6)], 1),
            ("multiple_objects", [EntityA(id=6), EntityA(id=7)], 2),
        ]
    )
    def test_find(self, name, return_value, expected_count):
        self.session.add_all(return_value)
        self.session.commit()
        result = self.repositoryA.find()
        self.assertEqual(len(result), expected_count)

    def test_find_with_filters(self):
        self.repositoryA.create(EntityA(id=6))
        self.repositoryA.create(EntityA(id=7))
        # Actually test filter
        result = self.repositoryA.find(filters={"id": 6})
        self.assertEqual(len(result), 1)

    def test_find_without_filters(self):
        self.repositoryA.create(EntityA(id=6))
        self.repositoryA.create(EntityA(id=7))
        # Actually test filter
        result = self.repositoryA.find()
        self.assertEqual(len(result), 2)

    def test_find_with_filters_no_results(self):
        self.repositoryA.create(EntityA(id=6))
        # Actually test filter
        result = self.repositoryA.find(filters={"id": 7})
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
