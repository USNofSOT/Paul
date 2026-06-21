import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Mock the database engine
mock_engine = MagicMock()

# Create a dummy module to hold the mock engine
mock_engine_module = ModuleType("src.data.engine")
mock_engine_module.engine = mock_engine

# Inject the mock module into sys.modules
sys.modules["src.data.engine"] = mock_engine_module


@pytest.fixture(autouse=True)
def mock_db_session():
    """Fixture to mock the database session globally for tests."""

    # Use a persistent mock object that tracks state
    class MockSession:
        def __init__(self):
            self.entities = {}  # Store "db" entities

        def query(self, model):
            self.current_model = model
            return self

        def filter(self, *args):
            return self

        def filter_by(self, **kwargs):
            return self

        def first(self):
            # If we've added an entity of this type, return it
            key = self.current_model.__name__
            if key in self.entities:
                return self.entities[key]

            # Create a default entity
            entity = MagicMock()
            # Set expected attributes based on test requirements
            entity.current_rank_id = 1
            entity.participant_rank_id = 1
            entity.host_rank_id = 1
            entity.gamertag = "TestTag"

            # Crucially, update this entity if it gets updated
            self.entities[key] = entity
            return entity

        def add(self, entity):
            # Add entity with a key derived from type
            key = type(entity).__name__
            self.entities[key] = entity

        def commit(self):
            # No-op
            pass

        def rollback(self):
            pass

        def execute(self, statement):
            # Handle update
            return MagicMock()  # Mock execution

        def close(self):
            pass

    mock_session = MockSession()

    # Mock the session factory
    from src.data.repository.common.base_repository import Session

    original_session = Session
    # Replace Session with a function that returns the mock_session
    import src.data.repository.common.base_repository
    src.data.repository.common.base_repository.Session = lambda: mock_session

    yield mock_session

    # Restore original Session factory
    src.data.repository.common.base_repository.Session = original_session
