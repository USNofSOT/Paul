import logging

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from data.engine import engine_string

from src.scheduler.jobs.task_heal_voyage_and_hosting_numbers import (
    heal_voyage_and_hosting_numbers,
)

log = logging.getLogger(__name__)
log_prefix = "[SCHEDULER]"


class Scheduler:
    """
    Singleton class to manage the scheduling of tasks.

    Attributes:
        _instance (Scheduler): The singleton instance of the Scheduler.
        scheduler (BackgroundScheduler): The APScheduler instance.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Scheduler, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the scheduler with job stores and executors.
        """
        try:
            jobstores = {"default": SQLAlchemyJobStore(url=engine_string)}
            executors = {"default": ThreadPoolExecutor(10)}
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores, executors=executors, timezone="UTC"
            )
            self.scheduler.remove_all_jobs()
        except Exception as e:
            log.error("%s Failed to initialize scheduler: %s", log_prefix, e)
            raise

    def start(self):
        """
        Start the scheduler and add jobs.
        """
        try:
            self.scheduler.add_job(
                name="heal_voyage_and_hosting_numbers",
                id="heal_voyage_and_hosting_numbers",
                replace_existing=True,
                func=heal_voyage_and_hosting_numbers,
                trigger="interval",
                days=2,
            )
            self.scheduler.start()
            log.info("%s Scheduler started successfully", log_prefix)
        except Exception as e:
            log.error("%s Failed to start scheduler: %s", log_prefix, e)
            raise
