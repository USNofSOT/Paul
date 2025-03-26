from data.model.awards_model import Awards
from data.repository.common.base_repository import BaseRepository


class AwardsRepository(BaseRepository):
    def __init__(self):
        super().__init__(Awards)

    def find_by_name(self, name: str) -> Awards | None:
        return self.find(filters={"name": name}, limit=1)[0]
