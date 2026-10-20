from __future__ import annotations

from src.utils.promotion.models import (
    PromotionEvaluation,
    RenderedField,
    RenderedPromotionSections,
    RequirementStatus,
)


class DefaultPromotionRenderer:
    def render(self, evaluation: PromotionEvaluation) -> RenderedPromotionSections:
        rank_url = evaluation.next_rank.rank_context.embed_url if evaluation.next_rank.rank_context else ""
        suffix = f"\n{rank_url}" if rank_url else ""

        fields = [
            RenderedField(
                name=f"Required Requirements - {evaluation.next_rank_display_name}{suffix}",
                value="\n".join(
                    line
                    for requirement in evaluation.required_requirements
                    for line in requirement.lines
                ),
            )
        ]

        if evaluation.additional_requirements:
            fields.append(
                RenderedField(
                    name=f"Additional Requirements - {evaluation.next_rank_display_name}",
                    value="\n".join(
                        line
                        for requirement in evaluation.additional_requirements
                        for line in requirement.lines
                    ),
                )
            )

        if evaluation.flavor_requirements:
            fields.append(
                RenderedField(
                    name=f"Notes - {evaluation.next_rank_display_name}",
                    value="\n".join(
                        line
                        for requirement in evaluation.flavor_requirements
                        for line in requirement.lines
                    ),
                )
            )

        required_statuses = {requirement.status for requirement in evaluation.required_requirements}
        return RenderedPromotionSections(
            fields=tuple(fields),
            has_required_failures=RequirementStatus.FAIL in required_statuses,
            has_required_information=RequirementStatus.INFO in required_statuses,
            has_required_successes=RequirementStatus.PASS in required_statuses,
            show_or_separator_after=evaluation.show_or_separator_after,
        )
