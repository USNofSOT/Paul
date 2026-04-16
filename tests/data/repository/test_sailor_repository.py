import os
import threading
import time
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.models import Sailor, Hosted, VoyageType
from src.data.repository.sailor_repository import ensure_sailor_exists


class TestSailorRepository(unittest.TestCase):
    def setUp(self):
        # Use a file-based SQLite database for concurrency testing
        self.db_path = f"test_db_{threading.get_ident()}_{int(time.time())}.db"
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False}
        )
        self.Session = sessionmaker(bind=self.engine)
        # Only create the tables we need for these tests
        Sailor.__table__.create(self.engine)
        Hosted.__table__.create(self.engine)

        # Patch the Session in base_repository
        import src.data.repository.common.base_repository
        self.original_session = src.data.repository.common.base_repository.Session
        src.data.repository.common.base_repository.Session = self.Session

    def tearDown(self):
        import src.data.repository.common.base_repository
        src.data.repository.common.base_repository.Session = self.original_session
        self.engine.dispose()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_ensure_sailor_exists_creates_new(self):
        sailor = ensure_sailor_exists(12345)
        self.assertIsNotNone(sailor)
        self.assertEqual(sailor.discord_id, 12345)

        # Verify it's in the DB
        session = self.Session()
        db_sailor = session.get(Sailor, 12345)
        self.assertIsNotNone(db_sailor)
        session.close()

    def test_ensure_sailor_exists_multiple_times(self):
        ensure_sailor_exists(12345)
        ensure_sailor_exists(12345)
        sailor = ensure_sailor_exists(12345)

        self.assertIsNotNone(sailor)
        self.assertEqual(sailor.discord_id, 12345)

    def test_concurrent_ensure_sailor_exists(self):
        results = []

        def call_ensure():
            try:
                res = ensure_sailor_exists(999)
                results.append(res)
            except Exception as e:
                results.append(e)

        threads = [threading.Thread(target=call_ensure) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for res in results:
            self.assertIsNotNone(res, "Result should not be None")
            if isinstance(res, Exception):
                self.fail(f"Concurrent ensure_sailor_exists failed with: {res}")
            self.assertEqual(res.discord_id, 999)

    def test_fk_issue_simulation(self):
        target_id = 111
        sailor = ensure_sailor_exists(target_id)
        self.assertIsNotNone(sailor)

        session = self.Session()
        # Use VoyageType.UNKNOWN instead of 'Unknown' to match the Enum
        voyage = Hosted(log_id=1, target_id=target_id, voyage_type=VoyageType.UNKNOWN)
        session.add(voyage)
        try:
            session.commit()
        except Exception as e:
            self.fail(f"Failed to add Hosted record after ensure_sailor_exists: {e}")
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
