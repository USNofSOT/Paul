import logging
import os

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

log = logging.getLogger(__name__)


def _sanitize_dsn_for_logs(dsn: str) -> str:
    try:
        return make_url(dsn).render_as_string(hide_password=True)
    except Exception:
        return "<redacted>"


def run_migrations(dsn: str) -> None:
    log.info("Running DB migrations on %r", _sanitize_dsn_for_logs(dsn))
    alembic_cfg = Config()
    alembic_cfg.set_main_option(
        "script_location", os.path.join(os.path.dirname(__file__))
    )
    alembic_cfg.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(alembic_cfg, "head")
    log.info("DB migrations complete")
