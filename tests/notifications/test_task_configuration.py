import random
import unittest

from src.cogs.tasks.task_process_command_notifications import ProcessCommandNotifications
from src.cogs.tasks.task_schedule_command_notifications import ScheduleCommandNotifications
from src.config.task_timing import (
    COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS,
    COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS,
    COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS,
)


class TestNotificationTaskConfiguration(unittest.TestCase):
    def test_scheduler_uses_configured_base_interval(self) -> None:
        self.assertEqual(
            ScheduleCommandNotifications.evaluate_notifications.hours,
            COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS,
        )
        self.assertIsNone(ScheduleCommandNotifications.evaluate_notifications.time)

    def test_scheduler_adds_jitter_within_configured_window(self) -> None:
        cog = object.__new__(ScheduleCommandNotifications)
        cog._random = random.Random(1234)

        additional_delay_seconds = cog._sample_additional_delay_seconds()
        max_additional_delay_seconds = (
                                               COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS
                                               - COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS
                                       ) * 60 * 60

        self.assertGreaterEqual(additional_delay_seconds, 0.0)
        self.assertLessEqual(additional_delay_seconds, max_additional_delay_seconds)

    def test_worker_uses_configured_interval(self) -> None:
        self.assertEqual(
            ProcessCommandNotifications.process_notifications.seconds,
            COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS,
        )
