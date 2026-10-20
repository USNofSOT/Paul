from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from src.data.repository.common.base_repository import BaseRepository

log = logging.getLogger(__name__)


class SystemRepository(BaseRepository[Any]):
    def __init__(self):
        # We don't have a specific entity type for system-wide ops
        super().__init__(Any)

    def get_process_list(self) -> list[dict[str, Any]]:
        rows = self.session.execute(text("SHOW PROCESSLIST")).mappings().all()
        return [dict(row) for row in rows]
