import unittest

from src.cogs.tasks.task_process_command_notifications import ProcessCommandNotifications
from src.cogs.tasks.task_schedule_command_notifications import ScheduleCommandNotifications
from src.config.task_timing import (
    COMMAND_NOTIFICATION_EVALUATOR_TASK_TIME,
    COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS,
)


class TestNotificationTaskConfiguration(unittest.TestCase):
    def test_scheduler_uses_configured_daily_time(self) -> None:
        self.assertIsNone(ScheduleCommandNotifications.evaluate_notifications.seconds)
        self.assertEqual(
            ScheduleCommandNotifications.evaluate_notifications.time,
            [COMMAND_NOTIFICATION_EVALUATOR_TASK_TIME],
        )

    def test_worker_uses_configured_interval(self) -> None:
        self.assertEqual(
            ProcessCommandNotifications.process_notifications.seconds,
            COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS,
        )
