from __future__ import annotations

from collections.abc import Callable

from src.data import RoleChangeType
from src.utils.promotion.models import (
    EvaluatedRequirement,
    PromotionContext,
    RequirementSpec,
    RequirementStatus,
)
from src.utils.rank_and_promotion_utils import has_award_or_higher
from src.utils.time_utils import format_time, get_time_difference, get_time_difference_in_days

STATUS_ICON = {
    RequirementStatus.PASS: ":white_check_mark:",
    RequirementStatus.FAIL: ":x:",
    RequirementStatus.INFO: "- ",
}


class AwardRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "award"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        status = RequirementStatus.PASS if has_award_or_higher(
            context.guild_member,
            spec.params["required_award"],
            spec.params["category_awards"],
        ) else RequirementStatus.FAIL
        return EvaluatedRequirement(status=status, lines=(f"{STATUS_ICON[status]} {spec.label}",))


class TrainingRoleRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "training_role"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        graduate_role_id = spec.params["graduate_role_id"]
        status = (
            RequirementStatus.PASS
            if graduate_role_id in context.netc_guild_member_role_ids
            else RequirementStatus.FAIL
        )
        return EvaluatedRequirement(status=status, lines=(f"{STATUS_ICON[status]} {spec.label}",))


class CountRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type in {"hosted_count", "voyage_count"}

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        current_value = context.hosted_count if spec.type == "hosted_count" else context.voyage_count
        required_value = spec.params["required_value"]
        status = RequirementStatus.PASS if current_value >= required_value else RequirementStatus.FAIL
        line = f"{STATUS_ICON[status]} {spec.label} ({current_value}/{required_value})"
        return EvaluatedRequirement(status=status, lines=(line,))


class RolePresenceRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "role_presence"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        role_ids = set(spec.params["role_ids"])
        match_mode = spec.params.get("match_mode", "any")
        if match_mode == "all":
            matched = role_ids.issubset(context.guild_member_role_ids)
        else:
            matched = bool(role_ids & context.guild_member_role_ids)

        status = RequirementStatus.PASS if matched else RequirementStatus.FAIL
        return EvaluatedRequirement(status=status, lines=(f"{STATUS_ICON[status]} {spec.label}",))


class ManualRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "manual"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        status = RequirementStatus(spec.params.get("status", RequirementStatus.INFO.value))
        return EvaluatedRequirement(status=status, lines=(f"{STATUS_ICON[status]} {spec.label}",))


class TimeInRankRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type in {"time_in_rank", "time_in_rank_max"}

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        role_id = spec.params["role_id"]
        role_log = context.audit_log_repository.get_latest_role_log_for_target_and_role(
            context.target_id,
            role_id,
        )
        warning_lines: list[str] = []
        if role_log is None:
            warning_lines.append(
                "\u200b \n **:warning: Please verify role age by hand whilst bot is new**  \n"
            )

        days_with_role = (
            get_time_difference_in_days(context.now, role_log.log_time) if role_log else 0
        )
        if role_log is None or role_log.change_type != RoleChangeType.ADDED:
            days_with_role = 0

        required_days = spec.params["required_days"]
        if spec.type == "time_in_rank":
            status = RequirementStatus.PASS if days_with_role >= required_days else RequirementStatus.FAIL
            line = f"{STATUS_ICON[status]} {spec.label} ({days_with_role}/{required_days})"
        else:
            status = RequirementStatus.FAIL if days_with_role >= required_days else RequirementStatus.INFO
            line = (
                f"{STATUS_ICON[status]} {spec.label} "
                f"({days_with_role} days, max {required_days} days)"
            )

        return EvaluatedRequirement(status=status, lines=tuple(warning_lines + [line]))


class RecentVoyageRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "recent_voyage"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        latest_voyage = context.voyage_repository.get_last_voyage_by_target_ids([context.target_id])
        voyage_time = latest_voyage.get(context.target_id) if latest_voyage else None
        if voyage_time is None:
            return EvaluatedRequirement(
                status=RequirementStatus.FAIL,
                lines=(f":x: {spec.label} (no recent voyage found)",),
            )

        days_since_voyage = get_time_difference_in_days(context.now, voyage_time)
        max_days = spec.params["max_days"]
        status = RequirementStatus.PASS if days_since_voyage <= max_days else RequirementStatus.FAIL
        line = (
            f"{STATUS_ICON[status]} {spec.label} "
            f"({format_time(get_time_difference(context.now, voyage_time))} ago)"
        )
        return EvaluatedRequirement(status=status, lines=(line,))


class CountAndTimeRequirementEvaluator:
    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "count_and_time"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        count_field = spec.params["count_field"]
        current_value = context.hosted_count if count_field == "hosted_count" else context.voyage_count
        required_value = spec.params["required_value"]
        role_id = spec.params["role_id"]
        role_log = context.audit_log_repository.get_latest_role_log_for_target_and_role(
            context.target_id,
            role_id,
        )
        days_with_role = (
            get_time_difference_in_days(context.now, role_log.log_time) if role_log else 0
        )
        if role_log is None or role_log.change_type != RoleChangeType.ADDED:
            days_with_role = 0

        required_days = spec.params["required_days"]
        status = (
            RequirementStatus.PASS
            if current_value >= required_value and days_with_role >= required_days
            else RequirementStatus.FAIL
        )
        line = (
            f"{STATUS_ICON[status]} {spec.label} "
            f"({current_value}/{required_value}, {days_with_role}/{required_days} days)"
        )
        return EvaluatedRequirement(status=status, lines=(line,), summary=spec.label)


class EitherOfRequirementEvaluator:
    def __init__(
            self,
            dispatcher: Callable[[RequirementSpec, PromotionContext], EvaluatedRequirement],
    ) -> None:
        self.dispatcher = dispatcher

    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "either_of"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        children = [
            self.dispatcher(child_spec, context)
            for child_spec in spec.params["requirements"]
        ]
        statuses = [child.status for child in children]
        if any(status == RequirementStatus.PASS for status in statuses):
            status = RequirementStatus.PASS
        elif any(status == RequirementStatus.INFO for status in statuses):
            status = RequirementStatus.INFO
        else:
            status = RequirementStatus.FAIL

        if spec.params.get("summary_only", False):
            return EvaluatedRequirement(status=status, lines=(f"{STATUS_ICON[status]} {spec.label}",))

        rendered_lines: list[str] = []
        for index, child in enumerate(children):
            rendered_lines.extend(child.lines)
            if index < len(children) - 1:
                rendered_lines.append("**OR**")

        return EvaluatedRequirement(status=status, lines=tuple(rendered_lines), summary=spec.label)


class ConditionalRoleRequirementEvaluator:
    def __init__(
            self,
            dispatcher: Callable[[RequirementSpec, PromotionContext], EvaluatedRequirement],
    ) -> None:
        self.dispatcher = dispatcher

    def supports(self, requirement_type: str) -> bool:
        return requirement_type == "conditional_role"

    def evaluate(
            self,
            spec: RequirementSpec,
            context: PromotionContext,
    ) -> EvaluatedRequirement:
        requirements = (
            spec.params["when_present"]
            if spec.params["role_id"] in context.guild_member_role_ids
            else spec.params["when_absent"]
        )
        rendered_lines: list[str] = []
        statuses: list[RequirementStatus] = []
        for requirement in requirements:
            evaluated = self.dispatcher(requirement, context)
            statuses.append(evaluated.status)
            rendered_lines.extend(evaluated.lines)

        if any(status == RequirementStatus.FAIL for status in statuses):
            status = RequirementStatus.FAIL
        elif any(status == RequirementStatus.INFO for status in statuses):
            status = RequirementStatus.INFO
        else:
            status = RequirementStatus.PASS
        return EvaluatedRequirement(status=status, lines=tuple(rendered_lines), summary=spec.label)
