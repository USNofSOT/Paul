import logging

from alembic import command
from alembic.config import Config

log = logging.getLogger(__name__)

def run_migrations(script_location: str, dsn: str) -> None:
    log.info('Running DB migrations in %r on %r', script_location, dsn)
    alembic_cfg = Config()
    alembic_cfg.set_main_option('script_location', script_location)
    alembic_cfg.set_main_option('sqlalchemy.url', dsn)
    command.upgrade(alembic_cfg, 'head')
    log.info('DB migrations complete')
