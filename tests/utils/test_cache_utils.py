import time
import unittest

from src.utils.cache_utils import ttl_cache


class TestTTLCache(unittest.TestCase):
    def test_cache_hits(self):
        # Arrange
        call_count = 0

        @ttl_cache(seconds=60)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Act
        self.assertEqual(my_func(1), 2)
        # Assert
        self.assertEqual(call_count, 1)

        # Act
        self.assertEqual(my_func(1), 2)
        # Assert
        self.assertEqual(call_count, 1)  # Should hit cache

        # Act
        self.assertEqual(my_func(2), 4)
        # Assert
        self.assertEqual(call_count, 2)  # New arg, should call

    def test_cache_expiration(self):
        # Arrange
        call_count = 0

        @ttl_cache(seconds=1)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Act
        self.assertEqual(my_func(1), 2)
        # Assert
        self.assertEqual(call_count, 1)

        # Arrange
        time.sleep(1.1)

        # Act
        self.assertEqual(my_func(1), 2)
        # Assert
        self.assertEqual(call_count, 2)  # Should have expired

    def test_cache_clear(self):
        # Arrange
        call_count = 0

        @ttl_cache(seconds=60)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Act
        self.assertEqual(my_func(1), 2)
        # Assert
        self.assertEqual(call_count, 1)

        # Act
        my_func.cache_clear()

        # Act
        self.assertEqual(my_func(1), 2)
        # Assert
        self.assertEqual(call_count, 2)  # Should have been cleared

    def test_maxsize(self):
        # Arrange
        call_count = 0

        @ttl_cache(seconds=60, maxsize=2)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Act
        my_func(1)  # cache: {1: ...}
        my_func(2)  # cache: {1: ..., 2: ...}
        # Assert
        self.assertEqual(call_count, 2)

        # Act
        my_func(3)  # cache: {2: ..., 3: ...} (1 should be removed)
        # Assert
        self.assertEqual(call_count, 3)

        # Act
        my_func(2)  # cache hit
        # Assert
        self.assertEqual(call_count, 3)

        # Act
        my_func(1)  # cache miss (was removed)
        # Assert
        self.assertEqual(call_count, 4)


if __name__ == "__main__":
    unittest.main()
