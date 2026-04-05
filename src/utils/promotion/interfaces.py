from __future__ import annotations

from typing import Protocol

from src.data.structs import NavyRank
from src.utils.promotion.models import (
    EvaluatedRequirement,
    PromotionContext,
    PromotionEvaluation,
    PromotionPathSpec,
    RenderedPromotionSections,
    RequirementSpec,
)


class PromotionPathProvider(Protocol):
    def get_paths(self, current_rank: NavyRank) -> list[PromotionPathSpec]:
        ...


class RequirementEvaluator(Protocol):
    def supports(self, requirement_type: str) -> bool:
        ...

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        ...


class PromotionRenderer(Protocol):
    def render(self, evaluation: PromotionEvaluation) -> RenderedPromotionSections:
        ...
