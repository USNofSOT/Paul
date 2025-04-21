from __future__ import annotations

from data.model.awards_model import Awards
from data.repository.common.base_repository import BaseRepository


class AwardsRepository(BaseRepository):
    def __init__(self):
        super().__init__(Awards)

    def find_by_name(self, name: str) -> Awards | None:
        try:
            return self.find(filters={"name": name}, limit=1)[0]
        except IndexError:
            return None

    def unique_categories(self) -> list[str]:
        return list({award.category for award in self.find()})
