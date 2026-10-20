from collections.abc import Iterable

from src.config.awards import REPRESENT_MEDALS
from src.config.representation import (
    ALL_REPRESENTATION_MANAGER_ROLE_IDS,
    HEAD_OF_MEDIA_ROLE_ID,
    HEAD_OF_SCHEDULING_ROLE_ID,
    XO_OF_MEDIA_ROLE_ID,
    XO_OF_SCHEDULING_ROLE_ID,
)
from src.data.models import RepresentationBadgeTier, RepresentationDepartment
from src.data.structs import Award

_OVERRIDE_ROLES = {"BOA", "NSC_ADMINISTRATOR"}
_ALL_MANAGER_ROLE_IDS = set(ALL_REPRESENTATION_MANAGER_ROLE_IDS)

REPRESENTATION_HEAD_ROLE_IDS_BY_DEPARTMENT: dict[RepresentationDepartment, int] = {
    RepresentationDepartment.MEDIA: HEAD_OF_MEDIA_ROLE_ID,
    RepresentationDepartment.SCHEDULING: HEAD_OF_SCHEDULING_ROLE_ID,
}
REPRESENTATION_ADD_ROLE_IDS_BY_DEPARTMENT: dict[RepresentationDepartment, tuple[int, ...]] = {
    RepresentationDepartment.MEDIA: (HEAD_OF_MEDIA_ROLE_ID, XO_OF_MEDIA_ROLE_ID),
    RepresentationDepartment.SCHEDULING: (HEAD_OF_SCHEDULING_ROLE_ID, XO_OF_SCHEDULING_ROLE_ID),
}


def get_representation_badge_tier(points: int) -> RepresentationBadgeTier:
    return RepresentationBadgeTier.from_points(points)


def get_next_representation_award(points: int) -> Award | None:
    for award in REPRESENT_MEDALS:
        if points < award.threshold:
            return award
    return None


def get_current_representation_award(points: int) -> Award | None:
    current_award = None
    for award in REPRESENT_MEDALS:
        if points >= award.threshold:
            current_award = award
        else:
            break
    return current_award


def get_representation_progress(points: int) -> tuple[int, int | None]:
    next_award = get_next_representation_award(points)
    next_threshold = next_award.threshold if next_award is not None else None
    return points, next_threshold


def can_view_representation_mod(
        actor_role_ids: Iterable[int],
        effective_roles: set[str],
) -> bool:
    return _has_override_role(effective_roles) or _has_any_role_id(
        actor_role_ids,
        _ALL_MANAGER_ROLE_IDS,
    )


def can_add_representation_points(
        actor_role_ids: Iterable[int],
        effective_roles: set[str],
        department: RepresentationDepartment,
) -> bool:
    if _has_override_role(effective_roles):
        return True
    return _has_any_role_id(
        actor_role_ids,
        REPRESENTATION_ADD_ROLE_IDS_BY_DEPARTMENT.get(department, ()),
    )


def can_remove_representation_points(
        actor_role_ids: Iterable[int],
        effective_roles: set[str],
        department: RepresentationDepartment,
) -> bool:
    if _has_override_role(effective_roles):
        return True
    head_role_id = REPRESENTATION_HEAD_ROLE_IDS_BY_DEPARTMENT.get(department)
    return head_role_id is not None and head_role_id in set(actor_role_ids)


def choose_representation_department(
        *,
        media_points: int,
        scheduling_points: int,
) -> RepresentationDepartment:
    if media_points > scheduling_points:
        return RepresentationDepartment.MEDIA
    return RepresentationDepartment.SCHEDULING


def is_representation_award_eligible(
        *,
        member_role_ids: set[int],
        eligible_role_id: int,
) -> bool:
    return eligible_role_id not in member_role_ids


def _has_override_role(effective_roles: set[str]) -> bool:
    return any(role in _OVERRIDE_ROLES for role in effective_roles)


def _has_any_role_id(
        actor_role_ids: Iterable[int],
        allowed_role_ids: Iterable[int],
) -> bool:
    allowed_role_id_set = set(allowed_role_ids)
    return any(role_id in allowed_role_id_set for role_id in actor_role_ids)
