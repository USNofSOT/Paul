from __future__ import annotations

from src.data.structs import NavyRank
from src.utils.promotion.models import PromotionPathSpec
from src.utils.promotion.specs import PROMOTION_PATHS_BY_RANK


class ConfigPromotionPathProvider:
    def get_paths(self, current_rank: NavyRank) -> list[PromotionPathSpec]:
        return list(PROMOTION_PATHS_BY_RANK.get(current_rank.index, ()))
