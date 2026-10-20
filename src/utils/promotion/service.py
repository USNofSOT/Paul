from __future__ import annotations

from src.utils.promotion.evaluators import (
    AwardRequirementEvaluator,
    ConditionalRoleRequirementEvaluator,
    CountAndTimeRequirementEvaluator,
    CountRequirementEvaluator,
    EitherOfRequirementEvaluator,
    ManualRequirementEvaluator,
    RecentVoyageRequirementEvaluator,
    RolePresenceRequirementEvaluator,
    TimeInRankRequirementEvaluator,
    TrainingRoleRequirementEvaluator,
)
from src.utils.promotion.interfaces import PromotionPathProvider, PromotionRenderer, RequirementEvaluator
from src.utils.promotion.models import (
    EvaluatedRequirement,
    PromotionContext,
    PromotionEvaluation,
    RenderedPromotionSections,
    RequirementSpec,
)
from src.utils.promotion.providers import ConfigPromotionPathProvider
from src.utils.promotion.renderer import DefaultPromotionRenderer
from src.utils.rank_and_promotion_utils import get_rank_by_index


class PromotionCheckService:
    def __init__(
            self,
            path_provider: PromotionPathProvider,
            evaluators: list[RequirementEvaluator],
            renderer: PromotionRenderer,
    ) -> None:
        self.path_provider = path_provider
        self.evaluators = evaluators
        self.renderer = renderer

    def evaluate(self, member_context: PromotionContext) -> list[RenderedPromotionSections]:
        sections: list[RenderedPromotionSections] = []
        for path in self.path_provider.get_paths(member_context.current_rank):
            next_rank = get_rank_by_index(path.next_rank_index)
            additional_requirements = path.additional_requirements
            if (
                    path.use_rank_additional_fallback
                    and not additional_requirements
                    and next_rank.rank_prerequisites
            ):
                additional_requirements = tuple(
                    RequirementSpec(
                        type="manual",
                        label=label,
                        params={"status": "info"},
                    )
                    for label in next_rank.rank_prerequisites.additional_requirements
                )

            flavor_requirements = path.flavor_requirements
            evaluation = PromotionEvaluation(
                next_rank=next_rank,
                next_rank_display_name=(
                    next_rank.marine_name if member_context.is_marine else next_rank.name
                ),
                required_requirements=tuple(
                    self._evaluate_requirement(requirement, member_context)
                    for requirement in path.required_requirements
                ),
                additional_requirements=tuple(
                    self._evaluate_requirement(requirement, member_context)
                    for requirement in additional_requirements
                ),
                flavor_requirements=tuple(
                    self._evaluate_requirement(requirement, member_context)
                    for requirement in flavor_requirements
                ),
                show_or_separator_after=path.show_or_separator_after,
            )
            sections.append(self.renderer.render(evaluation))
        return sections

    def _evaluate_requirement(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        for evaluator in self.evaluators:
            if evaluator.supports(spec.type):
                return evaluator.evaluate(spec, context)
        raise ValueError(f"Unsupported promotion requirement type: {spec.type}")


def build_default_promotion_check_service() -> PromotionCheckService:
    service = PromotionCheckService(
        path_provider=ConfigPromotionPathProvider(),
        evaluators=[],
        renderer=DefaultPromotionRenderer(),
    )
    service.evaluators = [
        AwardRequirementEvaluator(),
        TrainingRoleRequirementEvaluator(),
        CountRequirementEvaluator(),
        CountAndTimeRequirementEvaluator(),
        RolePresenceRequirementEvaluator(),
        ManualRequirementEvaluator(),
        TimeInRankRequirementEvaluator(),
        RecentVoyageRequirementEvaluator(),
        EitherOfRequirementEvaluator(service._evaluate_requirement),
        ConditionalRoleRequirementEvaluator(service._evaluate_requirement),
    ]
    return service
