import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

from src.utils.pocket_watch import (
    DEFAULT_POCKET_WATCH_THRESHOLDS,
    PocketWatchError,
    PocketWatchInsufficientDataError,
    _build_weekly_tick_positions,
    analyze_pocket_watch_activity,
    parse_timezone_label,
)


def make_voyage(timestamp: datetime) -> SimpleNamespace:
    return SimpleNamespace(log_time=timestamp)


class TestPocketWatch(unittest.TestCase):
    def test_build_weekly_tick_positions_limits_dense_labels(self):
        self.assertEqual(_build_weekly_tick_positions(0), [])
        self.assertEqual(_build_weekly_tick_positions(5), [0, 1, 2, 3, 4])
        tick_positions = _build_weekly_tick_positions(53)
        self.assertEqual(len(tick_positions), 53)
        self.assertEqual(tick_positions[0], 0)
        self.assertEqual(tick_positions[-1], 52)

    def test_build_weekly_tick_positions_respects_max_label_setting(self):
        tick_positions = _build_weekly_tick_positions(53, max_labels=12)
        self.assertEqual(tick_positions, [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 52])

    def test_parse_timezone_label_uses_saved_offset(self):
        timezone_info, label = parse_timezone_label("UTC+02:00 (EET)")

        self.assertEqual(label, "UTC+02:00 (EET)")
        self.assertEqual(
            datetime(2026, 1, 1, 12, 0, tzinfo=UTC).astimezone(timezone_info).hour,
            14,
        )

    def test_parse_timezone_label_falls_back_to_utc(self):
        timezone_info, label = parse_timezone_label("Not a timezone")

        self.assertEqual(label, "UTC")
        self.assertEqual(
            datetime(2026, 1, 1, 12, 0, tzinfo=UTC).astimezone(timezone_info).hour,
            12,
        )

    def test_analyze_pocket_watch_activity_rejects_invalid_days(self):
        with self.assertRaises(PocketWatchError):
            analyze_pocket_watch_activity(
                [make_voyage(datetime(2026, 1, 1, 12, 0, tzinfo=UTC))],
                days=DEFAULT_POCKET_WATCH_THRESHOLDS.max_days + 1,
            )

    def test_analyze_pocket_watch_activity_requires_enough_data(self):
        voyages = [
            make_voyage(datetime(2026, 1, 5, 12, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 12, 12, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 19, 12, 0, tzinfo=UTC)),
        ]

        with self.assertRaises(PocketWatchInsufficientDataError):
            analyze_pocket_watch_activity(
                voyages,
                days=90,
                now=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
            )

    def test_analyze_pocket_watch_activity_groups_activity_by_weekday_and_hour(self):
        voyages = [
            make_voyage(datetime(2026, 1, 5, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 6, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 13, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 14, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 20, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 21, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 27, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 28, 22, 0, tzinfo=UTC)),
        ]
        hosted = [
            make_voyage(datetime(2026, 1, 13, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 27, 22, 0, tzinfo=UTC)),
        ]

        analysis = analyze_pocket_watch_activity(
            voyages,
            hosted,
            days=90,
            timezone_value="UTC+02:00 (EET)",
            now=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(analysis.total_voyages, 8)
        self.assertEqual(analysis.total_hosted, 2)
        self.assertEqual(analysis.active_weeks, 4)
        self.assertEqual(analysis.active_hosted_weeks, 2)
        self.assertEqual(analysis.most_active_hour, 0)
        self.assertEqual(analysis.most_active_hour_label, "00:00-01:00")
        self.assertEqual(analysis.most_active_weekday_label, "Wed")
        self.assertEqual(analysis.most_active_hosted_hour_label, "00:00-01:00")
        self.assertEqual(analysis.most_active_hosted_weekday_label, "Wed")
        self.assertEqual(sum(analysis.weekly_attended_counts), 8)
        self.assertEqual(sum(analysis.weekly_hosted_counts), 2)

    def test_analyze_pocket_watch_activity_handles_no_hosting_data(self):
        voyages = [
            make_voyage(datetime(2026, 1, 5, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 6, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 13, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 14, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 20, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 21, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 27, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 28, 22, 0, tzinfo=UTC)),
        ]

        analysis = analyze_pocket_watch_activity(
            voyages,
            [],
            days=90,
            now=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(analysis.total_hosted, 0)
        self.assertEqual(analysis.active_hosted_weeks, 0)
        self.assertIsNone(analysis.first_hosted_at)
        self.assertIsNone(analysis.last_hosted_at)
        self.assertEqual(analysis.most_active_hosted_hour_label, "No activity")
        self.assertEqual(analysis.most_active_hosted_weekday_label, "No activity")
        self.assertEqual(analysis.average_hosted_per_week, 0.0)
        self.assertEqual(analysis.average_hosted_per_active_week, 0.0)

    def test_cache_payload_uses_date_window_for_stable_cache_keys(self):
        voyages = [
            make_voyage(datetime(2026, 1, 5, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 6, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 13, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 14, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 20, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 21, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 27, 22, 0, tzinfo=UTC)),
            make_voyage(datetime(2026, 1, 28, 22, 0, tzinfo=UTC)),
        ]

        analysis = analyze_pocket_watch_activity(
            voyages,
            days=90,
            now=datetime(2026, 3, 15, 12, 34, tzinfo=UTC),
        )

        payload = analysis.cache_payload(
            target_id=123,
            days=90,
            display_name="Test Sailor",
        )

        self.assertEqual(payload["window_start_date"], "2025-12-15")
        self.assertEqual(payload["window_end_date"], "2026-03-15")


if __name__ == "__main__":
    unittest.main()
