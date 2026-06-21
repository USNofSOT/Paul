import unittest
from datetime import date

from src.utils.streak_utils import compute_streaks


class TestComputeStreaks(unittest.TestCase):
    def test_empty_activity_returns_zeros(self):
        # Act
        current, longest, start, end, expiry = compute_streaks([], reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 0)
        self.assertEqual(longest, 0)
        self.assertIsNone(start)
        self.assertIsNone(end)
        self.assertIsNone(expiry)

    def test_active_streak_four_consecutive_days(self):
        # Arrange
        dates = [date(2026, 5, 1), date(2026, 4, 30), date(2026, 4, 29), date(2026, 4, 28)]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 4)
        self.assertEqual(longest, 4)
        self.assertEqual(start, date(2026, 4, 28))
        self.assertEqual(end, date(2026, 5, 1))
        self.assertEqual(expiry, date(2026, 5, 3))

    def test_broken_streak_returns_zero_current(self):
        # Last activity was Apr 28, today is May 1 — two full days ago → broken
        # Arrange
        dates = [date(2026, 4, 28), date(2026, 4, 27), date(2026, 4, 26)]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 0)
        self.assertEqual(longest, 3)
        self.assertEqual(start, date(2026, 4, 26))
        self.assertEqual(end, date(2026, 4, 28))
        self.assertIsNone(expiry)

    def test_grace_window_activity_yesterday_still_active(self):
        # Activity only yesterday (Apr 30), today is May 1 — must still count as active
        # Arrange
        dates = [date(2026, 4, 30)]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 1)
        self.assertEqual(longest, 1)
        self.assertEqual(start, date(2026, 4, 30))
        self.assertEqual(end, date(2026, 4, 30))
        self.assertEqual(expiry, date(2026, 5, 2))

    def test_activity_two_days_ago_is_broken(self):
        # Activity on Apr 29 only, today is May 1 — exactly the boundary
        # Arrange
        dates = [date(2026, 4, 29)]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 0)
        self.assertEqual(longest, 1)
        self.assertEqual(start, date(2026, 4, 29))
        self.assertEqual(end, date(2026, 4, 29))
        self.assertIsNone(expiry)

    def test_longest_streak_survives_after_break(self):
        # Arrange
        dates = [
            date(2026, 5, 1), date(2026, 4, 30),  # current 2-day run
            # gap: Apr 29 missing
            date(2026, 4, 28), date(2026, 4, 27), date(2026, 4, 26),
            date(2026, 4, 25), date(2026, 4, 24),  # older 5-day run
        ]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 2)
        self.assertEqual(longest, 5)
        self.assertEqual(start, date(2026, 4, 24))
        self.assertEqual(end, date(2026, 4, 28))
        self.assertEqual(expiry, date(2026, 5, 3))

    def test_single_day_streak_is_one_below_display_threshold(self):
        # A streak of 1 is valid but below the >=2 display threshold
        # Arrange
        dates = [date(2026, 5, 1)]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 1)
        self.assertEqual(longest, 1)
        self.assertEqual(start, date(2026, 5, 1))
        self.assertEqual(end, date(2026, 5, 1))
        self.assertEqual(expiry, date(2026, 5, 3))

    def test_expiry_is_two_days_after_most_recent_today(self):
        # Arrange
        dates = [date(2026, 5, 1), date(2026, 4, 30)]
        # Act
        _, _, _, _, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(expiry, date(2026, 5, 3))

    def test_expiry_is_two_days_after_yesterday_activity(self):
        # Arrange
        dates = [date(2026, 4, 30)]
        # Act
        _, _, _, _, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(expiry, date(2026, 5, 2))

    def test_longest_streak_with_multiple_gaps(self):
        # Arrange
        dates = [
            date(2026, 5, 1), date(2026, 4, 30),  # 2
            # gap 4-29
            date(2026, 4, 28), date(2026, 4, 27), date(2026, 4, 26),  # 3
            # gap 4-25
            date(2026, 4, 24), date(2026, 4, 23), date(2026, 4, 22), date(2026, 4, 21),  # 4
        ]
        # Act
        current, longest, start, end, expiry = compute_streaks(dates, reference_date=date(2026, 5, 1))
        # Assert
        self.assertEqual(current, 2)
        self.assertEqual(longest, 4)
        self.assertEqual(start, date(2026, 4, 21))
        self.assertEqual(end, date(2026, 4, 24))
        self.assertEqual(expiry, date(2026, 5, 3))


if __name__ == "__main__":
    unittest.main()
