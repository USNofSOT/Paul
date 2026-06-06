import logging

from sqlalchemy import desc

from src.data.models import (
    RepresentationDepartment,
    RepresentationPointMutation,
    RepresentationPoints,
    Sailor,
)
from src.data.repository.common.base_repository import BaseRepository
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)


def _coerce_reason(reason: str | None) -> str:
    cleaned_reason = (reason or "").strip()
    return cleaned_reason or "No reason provided."


class RepresentationRepository(BaseRepository[RepresentationPoints]):
    def __init__(self):
        super().__init__(RepresentationPoints)

    def ensure_sailor_exists(self, discord_id: int) -> Sailor:
        sailor = self.session.query(Sailor).filter(Sailor.discord_id == discord_id).first()
        if sailor is None:
            sailor = Sailor(discord_id=discord_id)
            self.session.add(sailor)
            self.session.flush()
        return sailor

    def get_or_create_points_record(self, target_id: int) -> RepresentationPoints:
        self.ensure_sailor_exists(target_id)

        points_record = (
            self.session.query(RepresentationPoints)
            .filter(RepresentationPoints.target_id == target_id)
            .first()
        )
        if points_record is None:
            points_record = RepresentationPoints(target_id=target_id)
            self.session.add(points_record)
            self.session.commit()
        return points_record

    def add_points(
            self,
            target_id: int,
            changed_by_id: int,
            department: RepresentationDepartment,
            amount: int = 1,
            reason: str | None = None,
    ) -> RepresentationPointMutation:
        if amount <= 0:
            raise ValueError("Representation point additions must be greater than zero.")
        return self._apply_points_delta(
            target_id=target_id,
            changed_by_id=changed_by_id,
            department=department,
            points_delta=amount,
            reason=reason,
        )

    def remove_points(
            self,
            target_id: int,
            changed_by_id: int,
            department: RepresentationDepartment,
            amount: int = 1,
            reason: str | None = None,
    ) -> RepresentationPointMutation:
        if amount <= 0:
            raise ValueError("Representation point removals must be greater than zero.")
        return self._apply_points_delta(
            target_id=target_id,
            changed_by_id=changed_by_id,
            department=department,
            points_delta=-amount,
            reason=reason,
        )

    def list_mutations(
            self,
            target_id: int,
            department: RepresentationDepartment | None = None,
            limit: int | None = None,
    ) -> list[RepresentationPointMutation]:
        query = (
            self.session.query(RepresentationPointMutation)
            .filter(RepresentationPointMutation.target_id == target_id)
            .order_by(desc(RepresentationPointMutation.created_at), desc(RepresentationPointMutation.id))
        )
        if department is not None:
            query = query.filter(RepresentationPointMutation.department == department)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_total_points(self, target_id: int) -> int:
        return self.get_or_create_points_record(target_id).total_representation_points

    def get_points_breakdown(self, target_id: int) -> RepresentationPoints:
        return self.get_or_create_points_record(target_id)

    def _apply_points_delta(
            self,
            target_id: int,
            changed_by_id: int,
            department: RepresentationDepartment,
            points_delta: int,
            reason: str | None,
    ) -> RepresentationPointMutation:
        if points_delta == 0:
            raise ValueError("Representation point updates cannot be zero.")

        try:
            self.ensure_sailor_exists(target_id)
            self.ensure_sailor_exists(changed_by_id)
            points_record = self.get_or_create_points_record(target_id)

            column_name = self._get_department_column_name(department)
            current_value = int(getattr(points_record, column_name) or 0)
            new_value = current_value + points_delta
            if new_value < 0:
                raise ValueError(
                    f"Cannot reduce {department.value} representation points below zero."
                )

            setattr(points_record, column_name, new_value)

            mutation = RepresentationPointMutation(
                target_id=target_id,
                changed_by_id=changed_by_id,
                department=department,
                points_delta=points_delta,
                reason=_coerce_reason(reason),
                created_at=utc_time_now(),
            )
            self.session.add(mutation)
            self.session.commit()
            return mutation
        except Exception as e:
            self.session.rollback()
            log.error("Failed to mutate representation points: %s", e)
            raise e

    @staticmethod
    def _get_department_column_name(department: RepresentationDepartment) -> str:
        department_columns: dict[RepresentationDepartment, str] = {
            RepresentationDepartment.MEDIA: "media_representation_points",
            RepresentationDepartment.SCHEDULING: "scheduling_representation_points",
        }
        try:
            return department_columns[department]
        except KeyError as exc:
            raise ValueError(f"Unsupported representation department: {department}") from exc
