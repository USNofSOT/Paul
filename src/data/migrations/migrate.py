import logging

from alembic import command
from alembic.config import Config

log = logging.getLogger(__name__)


def run_migrations(dsn: str) -> None:
    log.info("Running DB migrations on %r", dsn)
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "./data/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(alembic_cfg, "head")
    log.info("DB migrations complete")
