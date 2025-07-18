import unittest

import sqlalchemy
from parameterized import parameterized
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker

from src.data.repository.common.base_repository import BaseRepository

Base = sqlalchemy.orm.declarative_base()


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
            ("wrong_entity_for_A", EntityARepository(), [EntityB(), EntityA()]),
            ("wrong_entity_for_B", EntityBRepository(), [EntityA(), EntityB()]),
        ]
    )
    def test_create_multiple_wrong_entity_type(self, name, repository, entity):
        with self.assertRaises(TypeError):
            repository.create(entity)

    @parameterized.expand(
        [
            ("wrong_entity_for_A", EntityARepository(), EntityB()),
            ("wrong_entity_for_B", EntityBRepository(), EntityA()),
        ]
    )
    def test_update_wrong_entity_type(self, name, repository, entity):
        with self.assertRaises(TypeError):
            repository.update(entity)

    @parameterized.expand(
        [
            ("wrong_entity_for_A", EntityARepository(), [EntityB(), EntityA()]),
            ("wrong_entity_for_B", EntityBRepository(), [EntityA(), EntityB()]),
        ]
    )
    def test_update_multiple_wrong_entity_type(self, name, repository, entity):
        with self.assertRaises(TypeError):
            repository.update(entity)

    @parameterized.expand(
        [
            ("wrong_entity_for_A", EntityARepository(), EntityB()),
            ("wrong_entity_for_B", EntityBRepository(), EntityA()),
        ]
    )
    def test_remove_wrong_entity_type(self, name, repository, entity):
        with self.assertRaises(TypeError):
            repository.remove(entity)

    def create_multiple(self):
        entities = [EntityA(id=6), EntityA(id=7)]
        self.repositoryA.create(entities)
        self.assertEqual(entities[0].id, 6)
        self.assertEqual(entities[1].id, 7)
        res = self.session.query(EntityA).all()
        self.assertEqual(len(res), 2)

    def update_multiple(self):
        entities = [EntityA(id=6), EntityA(id=7)]
        self.repositoryA.create(entities)
        entities[0].id = 8
        entities[1].id = 9
        self.repositoryA.update(entities)
        res = self.session.query(EntityA).all()
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].id, 8)
        self.assertEqual(res[1].id, 9)

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

    @parameterized.expand(
        [
            ("filter_by_id_6_exists", {"id": 6}, 1, [EntityA(id=6), EntityA(id=7)]),
            ("filter_by_id_7_not_exists", {"id": 7}, 0, [EntityA(id=6)]),
            (
                "filter_by_name_test",
                {"name": "test"},
                2,
                [
                    EntityB(id=6, name="test"),
                    EntityB(id=7, name="test"),
                    EntityB(id=8, name="test2"),
                ],
            ),
            ("filter_by_nonexistent_id", {"id": 999}, 0, [EntityA(id=6), EntityA(id=7)]),
            ("filter_with_empty_conditions", {}, 2, [EntityA(id=6), EntityA(id=7)]),
            (
                "filter_by_multiple_conditions",
                {"id": 6, "name": "test"},
                1,
                [
                    EntityB(id=6, name="test"),
                    EntityB(id=7, name="test"),
                    EntityB(id=8, name="test2"),
                ],
            ),
            (
                "filter_by_name_nonexistent",
                {"name": "nonexistent"},
                0,
                [
                    EntityB(id=6, name="test"),
                    EntityB(id=7, name="test"),
                    EntityB(id=8, name="test2"),
                ],
            ),
            (
                "filter_by_partial_name",
                {"name": "tes"},
                0,
                [
                    EntityB(id=6, name="test"),
                    EntityB(id=7, name="test"),
                    EntityB(id=8, name="test2"),
                ],
            ),
        ]
    )
    def test_find_with_filters(self, name, filters, expected_count, entities):
        self.session.add_all(entities)
        self.session.commit()
        if "name" in filters:
            result = self.repositoryB.find(filters=filters)
        else:
            result = self.repositoryA.find(filters=filters)
        self.assertEqual(len(result), expected_count)

    def test_find_without_filters(self):
        self.repositoryA.create(EntityA(id=6))
        self.repositoryA.create(EntityA(id=7))
        result = self.repositoryA.find()
        self.assertEqual(len(result), 2)

    def test_find_with_limit(self):
        self.session.add_all([EntityA(id=6), EntityA(id=7)])
        self.session.commit()
        result = self.repositoryA.find(limit=1)
        self.assertEqual(len(result), 1)

    def test_find_with_skip(self):
        self.session.add_all([EntityA(id=6), EntityA(id=7)])
        self.session.commit()
        result = self.repositoryA.find(skip=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 7)

    def test_find_with_limit_and_skip(self):
        self.session.add_all([EntityA(id=6), EntityA(id=7), EntityA(id=8)])
        self.session.commit()
        result = self.repositoryA.find(limit=1, skip=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 7)


if __name__ == "__main__":
    unittest.main()
