import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError

from src.data.repository.common.base_repository import BaseRepository, _with_transient_retry


class TestEntity:
    pass


class MockRepository(BaseRepository[TestEntity]):
    def __init__(self, session=None):
        super().__init__(TestEntity, session)


class TestBaseRepositoryLifecycle(unittest.TestCase):
    def test_context_manager_closes_owned_session(self):
        with patch('src.data.repository.common.base_repository.Session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session

            with MockRepository() as repo:
                self.assertTrue(repo._owned_session)
                self.assertEqual(repo.session, mock_session)

            mock_session.close.assert_called_once()
            self.assertTrue(repo._closed)
            self.assertIsNone(repo.session)

    def test_context_manager_does_not_close_shared_session(self):
        mock_session = MagicMock()

        with MockRepository(session=mock_session) as repo:
            self.assertFalse(repo._owned_session)
            self.assertEqual(repo.session, mock_session)

        mock_session.close.assert_not_called()
        self.assertTrue(repo._closed)
        self.assertIsNone(repo.session)

    def test_runtime_error_when_closed(self):
        mock_session = MagicMock()
        repo = MockRepository(session=mock_session)
        repo.close_session()

        with self.assertRaises(RuntimeError):
            repo.find()

    def test_del_closes_owned_session(self):
        """__del__ must return the connection to the pool even when callers forget to close."""
        with patch('src.data.repository.common.base_repository.Session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session

            repo = MockRepository()
            self.assertFalse(repo._closed)
            repo.__del__()

            mock_session.close.assert_called_once()
            self.assertTrue(repo._closed)

    def test_del_does_not_close_shared_session(self):
        """__del__ must not close an injected session — that belongs to the caller."""
        mock_session = MagicMock()
        repo = MockRepository(session=mock_session)
        repo.__del__()

        mock_session.close.assert_not_called()
        self.assertTrue(repo._closed)

    def test_del_idempotent_after_explicit_close(self):
        """__del__ must be safe to call on an already-closed repository."""
        with patch('src.data.repository.common.base_repository.Session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session

            repo = MockRepository()
            repo.close_session()
            repo.__del__()  # must not raise or double-close

            mock_session.close.assert_called_once()

    def test_close_session_idempotent(self):
        mock_session = MagicMock()
        repo = MockRepository(session=mock_session)
        repo.close_session()
        repo.close_session()  # second call must be a no-op

        mock_session.close.assert_not_called()

    # --- Transient retry ---

    def test_transient_retry_success(self):
        mock_session = MagicMock()
        orig_error = MagicMock()
        orig_error.args = (2006,)  # MySQL server has gone away
        error = OperationalError("statement", "params", orig_error)

        mock_method = MagicMock()
        mock_method.side_effect = [error, error, "success"]

        class RetryRepo(MockRepository):
            @_with_transient_retry
            def do_work(self):
                return mock_method()

        with patch('time.sleep'):
            result = RetryRepo(session=mock_session).do_work()

        self.assertEqual(result, "success")
        self.assertEqual(mock_method.call_count, 3)
        self.assertEqual(mock_session.rollback.call_count, 2)

    def test_transient_retry_eventual_failure(self):
        mock_session = MagicMock()
        orig_error = MagicMock()
        orig_error.args = (2006,)
        error = OperationalError("statement", "params", orig_error)

        mock_method = MagicMock(side_effect=error)

        class RetryRepo(MockRepository):
            @_with_transient_retry
            def do_work(self):
                return mock_method()

        with patch('time.sleep'), self.assertRaises(OperationalError):
            RetryRepo(session=mock_session).do_work()

        self.assertEqual(mock_method.call_count, 3)

    def test_non_transient_error_no_retry(self):
        mock_session = MagicMock()
        orig_error = MagicMock()
        orig_error.args = (1045,)  # Access denied — not retried
        error = OperationalError("statement", "params", orig_error)

        mock_method = MagicMock(side_effect=error)

        class RetryRepo(MockRepository):
            @_with_transient_retry
            def do_work(self):
                return mock_method()

        with patch('time.sleep'), self.assertRaises(OperationalError):
            RetryRepo(session=mock_session).do_work()

        self.assertEqual(mock_method.call_count, 1)

    def test_all_transient_codes_are_retried(self):
        """Each error code that represents a recoverable DB error must trigger retry."""
        for code in (1213, 1205, 2006, 2013):
            with self.subTest(code=code):
                mock_session = MagicMock()
                orig_error = MagicMock()
                orig_error.args = (code,)
                error = OperationalError("statement", "params", orig_error)

                mock_method = MagicMock()
                mock_method.side_effect = [error, "ok"]

                class RetryRepo(MockRepository):
                    @_with_transient_retry
                    def do_work(self):
                        return mock_method()

                with patch('time.sleep'):
                    result = RetryRepo(session=mock_session).do_work()

                self.assertEqual(result, "ok")
                self.assertEqual(mock_method.call_count, 2)
                mock_method.reset_mock()

    def test_error_without_orig_is_not_retried(self):
        """OperationalError with no .orig attribute must not be retried."""
        mock_session = MagicMock()
        error = OperationalError("statement", "params", None)
        # Remove orig attribute to simulate the no-orig case
        error.orig = None

        mock_method = MagicMock(side_effect=error)

        class RetryRepo(MockRepository):
            @_with_transient_retry
            def do_work(self):
                return mock_method()

        with patch('time.sleep'), self.assertRaises(OperationalError):
            RetryRepo(session=mock_session).do_work()

        self.assertEqual(mock_method.call_count, 1)


if __name__ == "__main__":
    unittest.main()
