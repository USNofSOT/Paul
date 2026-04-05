from __future__ import annotations

from src.config.awards import (
    CITATION_OF_COMBAT,
    CITATION_OF_CONDUCT,
    COMBAT_MEDALS,
    CONDUCT_MEDALS,
    FOUR_MONTHS_SERVICE_STRIPES,
    HONORABLE_CONDUCT,
    HOSTED_MEDALS,
    LEGION_OF_CONDUCT,
    MARITIME_SERVICE_MEDAL,
    NCO_IMPROVEMENT_RIBBON,
    SERVICE_STRIPES,
)
from src.config.netc_server import (
    COSA_GRADUATE_ROLE,
    JLA_GRADUATE_ROLE,
    OCS_GRADUATE_ROLE,
    SLA_GRADUATE_ROLE,
    SOCS_GRADUATE_ROLE,
)
from src.config.ranks_roles import (
    NAVAL_SPECIALIST_ROLE,
    E2_ROLES,
    E3_ROLES,
    E6_ROLES,
    O1_ROLES,
    O4_ROLES,
    O5_ROLES,
    SPD_ROLES,
    SHIP_SL_ROLE,
    SQUAD_XO_ROLE,
)
from src.utils.promotion.models import PromotionPathSpec, RequirementSpec


def award_requirement(label: str, required_award, category_awards) -> RequirementSpec:
    return RequirementSpec(
        type="award",
        label=label,
        params={"required_award": required_award, "category_awards": category_awards},
    )


def training_role_requirement(label: str, graduate_role_id: int) -> RequirementSpec:
    return RequirementSpec(
        type="training_role",
        label=label,
        params={"graduate_role_id": graduate_role_id},
    )


def hosted_count_requirement(label: str, required_value: int) -> RequirementSpec:
    return RequirementSpec(
        type="hosted_count",
        label=label,
        params={"required_value": required_value},
    )


def voyage_count_requirement(label: str, required_value: int) -> RequirementSpec:
    return RequirementSpec(
        type="voyage_count",
        label=label,
        params={"required_value": required_value},
    )


def role_presence_requirement(label: str, *role_ids: int, match_mode: str = "any") -> RequirementSpec:
    return RequirementSpec(
        type="role_presence",
        label=label,
        params={"role_ids": role_ids, "match_mode": match_mode},
    )


def manual_requirement(label: str, status: str = "info") -> RequirementSpec:
    return RequirementSpec(type="manual", label=label, params={"status": status})


def time_in_rank_requirement(label: str, role_id: int, required_days: int) -> RequirementSpec:
    return RequirementSpec(
        type="time_in_rank",
        label=label,
        params={"role_id": role_id, "required_days": required_days},
    )


def time_in_rank_max_requirement(label: str, role_id: int, required_days: int) -> RequirementSpec:
    return RequirementSpec(
        type="time_in_rank_max",
        label=label,
        params={"role_id": role_id, "required_days": required_days},
    )


def recent_voyage_requirement(label: str, max_days: int) -> RequirementSpec:
    return RequirementSpec(
        type="recent_voyage",
        label=label,
        params={"max_days": max_days},
    )


def count_and_time_requirement(
        label: str,
        count_field: str,
        required_value: int,
        role_id: int,
        required_days: int,
) -> RequirementSpec:
    return RequirementSpec(
        type="count_and_time",
        label=label,
        params={
            "count_field": count_field,
            "required_value": required_value,
            "role_id": role_id,
            "required_days": required_days,
        },
    )


def either_of_requirement(
        label: str,
        *requirements: RequirementSpec,
        summary_only: bool = False,
) -> RequirementSpec:
    return RequirementSpec(
        type="either_of",
        label=label,
        params={"requirements": requirements, "summary_only": summary_only},
    )


def conditional_role_requirement(
        label: str,
        role_id: int,
        when_present: tuple[RequirementSpec, ...],
        when_absent: tuple[RequirementSpec, ...],
) -> RequirementSpec:
    return RequirementSpec(
        type="conditional_role",
        label=label,
        params={
            "role_id": role_id,
            "when_present": when_present,
            "when_absent": when_absent,
        },
    )


PROMOTION_PATHS_BY_RANK: dict[int, tuple[PromotionPathSpec, ...]] = {
    2: (
        PromotionPathSpec(
            next_rank_index=3,
            required_requirements=(
                conditional_role_requirement(
                    label="Seaman promotion path",
                    role_id=E2_ROLES[1],
                    when_present=(
                        time_in_rank_max_requirement(
                            "Has been a Seaman Apprentice for",
                            E2_ROLES[1],
                            14,
                        ),
                        recent_voyage_requirement("Had a voyage in the last 14 days", 14),
                    ),
                    when_absent=(
                        voyage_count_requirement("Go on five voyages", 5),
                        either_of_requirement(
                            "Awarded Citation of Conduct or Citation of Combat",
                            award_requirement(
                                f"Awarded <@&{CITATION_OF_CONDUCT.role_id}>",
                                CITATION_OF_CONDUCT,
                                CONDUCT_MEDALS,
                            ),
                            award_requirement(
                                f"Awarded <@&{CITATION_OF_COMBAT.role_id}>",
                                CITATION_OF_COMBAT,
                                COMBAT_MEDALS,
                            ),
                            summary_only=True,
                        ),
                    ),
                ),
            ),
        ),
    ),
    3: (
        PromotionPathSpec(
            next_rank_index=4,
            required_requirements=(
                either_of_requirement(
                    "Complete either E-4 voyage path",
                    count_and_time_requirement(
                        "Go on twenty voyages and wait one week as an E-3",
                        "voyage_count",
                        20,
                        E3_ROLES[0],
                        7,
                    ),
                    count_and_time_requirement(
                        "Go on fifteen voyages and wait two weeks as an E-3",
                        "voyage_count",
                        15,
                        E3_ROLES[0],
                        14,
                    ),
                ),
                training_role_requirement("Is a JLA Graduate", JLA_GRADUATE_ROLE),
                award_requirement(
                    f"Awarded <@&{CITATION_OF_CONDUCT.role_id}>",
                    CITATION_OF_CONDUCT,
                    CONDUCT_MEDALS,
                ),
            ),
        ),
    ),
    4: (
        PromotionPathSpec(
            next_rank_index=5,
            required_requirements=(
                award_requirement(
                    f"Awarded <@&{LEGION_OF_CONDUCT.role_id}>",
                    LEGION_OF_CONDUCT,
                    CONDUCT_MEDALS,
                ),
                role_presence_requirement(
                    f"Awarded <@&{NCO_IMPROVEMENT_RIBBON.role_id}>",
                    NCO_IMPROVEMENT_RIBBON.role_id,
                ),
                training_role_requirement("Is an SLA Graduate", SLA_GRADUATE_ROLE),
                hosted_count_requirement("Hosted ten voyages", 10),
            ),
            additional_requirements=(
                either_of_requirement(
                    "Joined an SPD or became a Naval Specialist",
                    role_presence_requirement("Joined an SPD", *SPD_ROLES),
                    role_presence_requirement(
                        "Became a Naval Specialist",
                        NAVAL_SPECIALIST_ROLE,
                    ),
                    summary_only=True,
                ),
                either_of_requirement(
                    "Applied for XO to a squad or became a squad leader (when available)",
                    role_presence_requirement("Holds the Squad XO role", SQUAD_XO_ROLE),
                    role_presence_requirement("Became a Squad Leader", SHIP_SL_ROLE),
                    summary_only=True,
                ),
            ),
        ),
    ),
    5: (
        PromotionPathSpec(
            next_rank_index=6,
            required_requirements=(
                time_in_rank_requirement("Waited one month as an E-6", E6_ROLES[0], 30),
                hosted_count_requirement("Hosted twenty voyages", 20),
            ),
            additional_requirements=(
                either_of_requirement(
                    "Joined an SPD or became a Naval Specialist",
                    role_presence_requirement("Joined an SPD", *SPD_ROLES),
                    role_presence_requirement(
                        "Became a Naval Specialist",
                        NAVAL_SPECIALIST_ROLE,
                    ),
                    summary_only=True,
                ),
                role_presence_requirement("Became a Squad Leader", SHIP_SL_ROLE),
                manual_requirement("Passed the SNCO Board"),
            ),
        ),
    ),
    6: (
        PromotionPathSpec(
            next_rank_index=8,
            required_requirements=(
                training_role_requirement("Is a COSA Graduate", COSA_GRADUATE_ROLE),
                award_requirement(
                    f"Awarded <@&{HONORABLE_CONDUCT.role_id}>",
                    HONORABLE_CONDUCT,
                    CONDUCT_MEDALS,
                ),
                award_requirement(
                    f"Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}>",
                    FOUR_MONTHS_SERVICE_STRIPES,
                    SERVICE_STRIPES,
                ),
            ),
            additional_requirements=(
                manual_requirement("Interviewed for a CoS position"),
                role_presence_requirement("Joined an SPD", *SPD_ROLES),
            ),
            show_or_separator_after=True,
        ),
        PromotionPathSpec(
            next_rank_index=9,
            required_requirements=(
                training_role_requirement("Is a COSA Graduate", COSA_GRADUATE_ROLE),
                award_requirement(
                    f"Awarded <@&{HONORABLE_CONDUCT.role_id}>",
                    HONORABLE_CONDUCT,
                    CONDUCT_MEDALS,
                ),
                award_requirement(
                    f"Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}>",
                    FOUR_MONTHS_SERVICE_STRIPES,
                    SERVICE_STRIPES,
                ),
                hosted_count_requirement("Hosted thirty-five official voyages", 35),
            ),
            additional_requirements=(manual_requirement("Passed the Officer Board"),),
        ),
    ),
    8: (
        PromotionPathSpec(
            next_rank_index=9,
            required_requirements=(
                training_role_requirement("Is a COSA Graduate", COSA_GRADUATE_ROLE),
                award_requirement(
                    f"Awarded <@&{HONORABLE_CONDUCT.role_id}>",
                    HONORABLE_CONDUCT,
                    CONDUCT_MEDALS,
                ),
                award_requirement(
                    f"Awarded <@&{FOUR_MONTHS_SERVICE_STRIPES.role_id}>",
                    FOUR_MONTHS_SERVICE_STRIPES,
                    SERVICE_STRIPES,
                ),
                hosted_count_requirement("Hosted thirty-five official voyages", 35),
            ),
            additional_requirements=(manual_requirement("Passed the Officer Board"),),
        ),
    ),
    9: (
        PromotionPathSpec(
            next_rank_index=10,
            required_requirements=(
                time_in_rank_requirement("Waited two weeks as an O1", O1_ROLES[0], 14),
                training_role_requirement("Is an OCS Graduate", OCS_GRADUATE_ROLE),
            ),
        ),
    ),
    10: (
        PromotionPathSpec(
            next_rank_index=11,
            required_requirements=(training_role_requirement("Is an SOCS Graduate", SOCS_GRADUATE_ROLE),),
        ),
    ),
    11: (
        PromotionPathSpec(
            next_rank_index=12,
            required_requirements=(time_in_rank_requirement("Waited four weeks as an O4", O4_ROLES[0], 28),),
            additional_requirements=(
                manual_requirement(
                    "Recruited and maintained 4 members from outside the server on their ship, not including CO/XO/CoS"
                ),
                manual_requirement(
                    "Built a functional chain of command on their ship that can fulfill ship duties despite being incomplete"
                ),
            ),
        ),
    ),
    12: (
        PromotionPathSpec(
            next_rank_index=13,
            required_requirements=(
                time_in_rank_requirement("Waited three months as an O5", O5_ROLES[0], 90),
                award_requirement(
                    f"Awarded <@&{MARITIME_SERVICE_MEDAL.role_id}>",
                    MARITIME_SERVICE_MEDAL,
                    HOSTED_MEDALS,
                ),
            ),
            additional_requirements=(
                manual_requirement("Maintains a very active ship"),
                manual_requirement("Built a full chain of command"),
            ),
        ),
    ),
    13: (
        PromotionPathSpec(
            next_rank_index=14,
            required_requirements=(manual_requirement("Must bribe the Admiral", status="fail"),),
        ),
    ),
    14: (
        PromotionPathSpec(
            next_rank_index=15,
            required_requirements=(manual_requirement("Selected by the AOTN"),),
            additional_requirements=(
                manual_requirement("Has to give flag ship command to another SO"),
            ),
        ),
    ),
    15: (
        PromotionPathSpec(
            next_rank_index=16,
            required_requirements=(manual_requirement("Must bribe the Admiral", status="fail"),),
        ),
    ),
    16: (
        PromotionPathSpec(
            next_rank_index=101,
            required_requirements=(
                manual_requirement(
                    "Viewed [training video #1](https://www.youtube.com/watch?v=dQw4w9WgXcQ)",
                    status="fail",
                ),
            ),
        ),
    ),
}
