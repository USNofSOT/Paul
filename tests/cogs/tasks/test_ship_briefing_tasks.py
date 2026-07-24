import asyncio
import unittest
from unittest.mock import patch

from src.cogs.tasks.task_check_boa_awards import CheckBoaAwardsTask
from src.cogs.tasks.task_check_representation_awards import (
    AutoCheckRepresentationAwards,
)
from src.cogs.tasks.task_check_training_awards import AutoCheckAwardsTraining
from src.cogs.tasks.task_ship_daily_briefing import ShipDailyBriefingTask
from src.cogs.tasks.task_ship_weekly_briefing import ShipWeeklyBriefingTask
from src.config.briefings import (
    DAILY_BRIEFING_CONCERNS,
    DAILY_BRIEFING_TIME,
    WEEKLY_BRIEFING_CONCERNS,
    WEEKLY_BRIEFING_TIME,
    WEEKLY_BRIEFING_WEEKDAY,
)


class TestShipBriefingTaskConfiguration(unittest.TestCase):
    def test_daily_briefing_uses_configured_time(self):
        self.assertEqual(
            ShipDailyBriefingTask.ship_daily_briefing.time,
            [DAILY_BRIEFING_TIME],
        )

    def test_weekly_briefing_uses_configured_time(self):
        self.assertEqual(
            ShipWeeklyBriefingTask.ship_weekly_briefing.time,
            [WEEKLY_BRIEFING_TIME],
        )
        self.assertEqual(WEEKLY_BRIEFING_WEEKDAY, 4)

    def test_briefing_concerns_are_small_and_explicit(self):
        self.assertEqual(
            DAILY_BRIEFING_CONCERNS,
            {"requirements": True, "awards": True},
        )
        self.assertEqual(
            WEEKLY_BRIEFING_CONCERNS,
            {"activity": True, "crew": True},
        )

    def test_unhandled_task_errors_notify_engineers(self):
        error = RuntimeError("database unavailable")
        callbacks = (
            (
                ShipDailyBriefingTask.ship_daily_briefing_error,
                "src.cogs.tasks.task_ship_daily_briefing.log",
            ),
            (
                ShipWeeklyBriefingTask.ship_weekly_briefing_error,
                "src.cogs.tasks.task_ship_weekly_briefing.log",
            ),
            (
                CheckBoaAwardsTask.check_boa_awards_error,
                "src.cogs.tasks.task_check_boa_awards.log",
            ),
            (
                AutoCheckAwardsTraining.my_task_error,
                "src.cogs.tasks.task_check_training_awards.log",
            ),
            (
                AutoCheckRepresentationAwards.my_task_error,
                "src.cogs.tasks.task_check_representation_awards.log",
            ),
        )

        for callback, logger_path in callbacks:
            with (
                self.subTest(callback=callback.__name__),
                patch(logger_path) as task_log,
            ):
                asyncio.run(callback(None, error))

                self.assertIs(
                    task_log.error.call_args.kwargs["exc_info"],
                    error,
                )
                self.assertTrue(
                    task_log.error.call_args.kwargs["extra"]["notify_engineer"]
                )
