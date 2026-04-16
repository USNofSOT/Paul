import logging
from datetime import datetime
from typing import Type

from src.config.main_server import NRC_RECORDS_CHANNEL
from src.config.netc_server import (
    COSA_RECORDS_CHANNEL,
    JLA_RECORDS_CHANNEL,
    LEGACY_NETC_RECORDS_CHANNELS,
    NETC_RECORDS_CHANNELS,
    OCS_RECORDS_CHANNEL,
    SLA_RECORDS_CHANNEL,
    SNLA_RECORDS_CHANNEL,
    SOCS_RECORDS_CHANNEL,
)
from src.config.spd_servers import ST_RECORDS_CHANNEL
from src.data import Sailor, Training, TrainingCategory, TrainingRecord, TraingType
from src.data.repository.common.base_repository import BaseRepository

log = logging.getLogger(__name__)

TRAINING_TYPE_BY_RECORDS_CHANNEL = {
    JLA_RECORDS_CHANNEL: TraingType.JLA,
    SNLA_RECORDS_CHANNEL: TraingType.SNLA,
    SLA_RECORDS_CHANNEL: TraingType.SLA,
    COSA_RECORDS_CHANNEL: TraingType.COSA,
    OCS_RECORDS_CHANNEL: TraingType.OCS,
    SOCS_RECORDS_CHANNEL: TraingType.SOCS,
    NRC_RECORDS_CHANNEL: TraingType.NRC,
    ST_RECORDS_CHANNEL: TraingType.ST,
}
NETC_TRAINING_POINT_FIELDS_BY_TYPE = {
    TraingType.JLA: "jla_training_points",
    TraingType.SNLA: "snla_training_points",
    TraingType.SLA: "sla_training_points",
    TraingType.COSA: "cosa_training_points",
    TraingType.OCS: "ocs_training_points",
    TraingType.SOCS: "socs_training_points",
}


def is_netc_records_channel(log_channel_id: int) -> bool:
    return (
            log_channel_id in NETC_RECORDS_CHANNELS
            or log_channel_id in LEGACY_NETC_RECORDS_CHANNELS
    )


def get_training_category_for_channel(log_channel_id: int) -> TrainingCategory:
    return (
        TrainingCategory.NETC
        if is_netc_records_channel(log_channel_id)
        else TrainingCategory.NRC
    )


def get_training_type_for_channel(log_channel_id: int) -> TraingType:
    return TRAINING_TYPE_BY_RECORDS_CHANNEL.get(log_channel_id, TraingType.NRC)


def _adjust_training_record_points(
        training_record: TrainingRecord,
        attribute_name: str,
        delta: int,
        target_id: int,
        label: str,
) -> None:
    old_value = getattr(training_record, attribute_name, 0)
    new_value = max(0, old_value + delta)
    setattr(training_record, attribute_name, new_value)
    action = "Incremented" if delta > 0 else "Decremented"
    log.info(
        "%s %s training points for %s from %s to %s",
        action,
        label,
        target_id,
        old_value,
        new_value,
    )


def _apply_training_delta(training_record: TrainingRecord, training: Training, delta: int) -> None:
    if training.training_type == TraingType.ST:
        _adjust_training_record_points(
            training_record, "st_training_points", delta, training.target_id, "ST"
        )
        return

    if training.training_category == TrainingCategory.NRC:
        _adjust_training_record_points(
            training_record, "nrc_training_points", delta, training.target_id, "NRC"
        )
        return

    if training.training_category != TrainingCategory.NETC:
        return

    _adjust_training_record_points(
        training_record, "netc_training_points", delta, training.target_id, "NETC"
    )
    point_field = NETC_TRAINING_POINT_FIELDS_BY_TYPE.get(training.training_type)
    if point_field is not None:
        _adjust_training_record_points(
            training_record,
            point_field,
            delta,
            training.target_id,
            training.training_type.value,
        )


class TrainingRecordsRepository(BaseRepository[TrainingRecord]):
    def __init__(self):
        super().__init__(TrainingRecord)

    def get_or_create_training_record(self, target_id: int) -> TrainingRecord:
        try:
            # First we want to ensure that a sailor exists in the database
            sailor = self.session.query(Sailor).filter(Sailor.discord_id == target_id).first()
            if not sailor:
                sailor = Sailor(discord_id=target_id)
                self.session.add(sailor)
                self.session.commit()

            # Now we want to check if a training record exists for this sailor
            training_record = self.session.query(TrainingRecord).filter(
                TrainingRecord.target_id == sailor.discord_id).first()
            if not training_record:
                training_record = TrainingRecord(target_id=sailor.discord_id)
                self.session.add(training_record)
                self.session.commit()

            return training_record
        except Exception as e:
            log.error(f"Failed to get or create training record: {e}")
            raise e

    def get_training_record_by_log_id(self, log_id: int) -> Type[TrainingRecord]:
        try:
            result = (
                self.session.query(TrainingRecord)
                .join(Training, TrainingRecord.target_id == Training.target_id)
                .filter(Training.log_id == log_id)
                .one_or_none()
            )
            if result is None:
                raise ValueError(f"No training record found for log_id {log_id}")

            return result
        except Exception as e:
            log.error(f"Failed to get training record by log id {log_id}: {e}")
            raise

    def save_training(self, log_id: int, target_id: int, log_channel_id: int, log_time: datetime = None) -> Type[Training]:
        try:
            log_time = datetime.now() if not log_time else log_time
            # 1. Make sure training_record exists
            self.get_or_create_training_record(target_id)

            # 1. Check if the training already exists
            training = self.session.query(Training).filter(Training.log_id == log_id).first()
            if training:
                raise ValueError("Training record already exists")

            # 2. Create a new training record
            training_category = get_training_category_for_channel(log_channel_id)
            training_type = get_training_type_for_channel(log_channel_id)
            training = Training(log_id=log_id, target_id=target_id, log_channel_id=log_channel_id, log_time=log_time, training_type=training_type, training_category=training_category)
            self.session.add(training)
            self.session.commit()

            # 3. Increment the training points
            self._increment_training_points(training)

            # 4. Return the training record
            return training
        except Exception as e:
            self.session.rollback()
            log.error(f"Failed to save training: {e}")
            raise e

    def delete_training(self, log_id: int, log_channel_id: int) -> Type[Training]:
        try:
            # 1. Get the training record for the user
            training_record = self.get_training_record_by_log_id(log_id)
            if not training_record:
                raise ValueError("Training record not found")
            target_id = training_record.target_id or 0

            # 1. Get the training
            training = self.session.query(Training).filter(Training.log_id == log_id).first()
            if not training:
                raise ValueError("Training record not found")

            # 2. Delete the training record
            self.session.delete(training)
            self.session.commit()

            # 3. Decrement the training points
            self._decrement_training_points(training)

            # 4. Return the training record
            return training
        except Exception as e:
            self.session.rollback()
            log.error(f"Failed to delete training: {e}")
            raise e

    def _increment_training_points(self, training: Training):
        try:
            training_record = self.get_or_create_training_record(training.target_id)

            log.info(f"Incrementing training points for {training.target_id}")
            _apply_training_delta(training_record, training, 1)

            log.info(f"Committing training points for {training.target_id}")
            self.session.commit()
        except Exception as e:
            log.error(f"Failed to increment training points: {e}")
            raise e

    def _decrement_training_points(self, training: Training):
        try:
            training_record = self.get_or_create_training_record(training.target_id)

            log.info(f"Decrementing training points for {training.target_id}")
            _apply_training_delta(training_record, training, -1)
            log.info(f"Committing training points for {training.target_id}")
            self.session.commit()
        except Exception as e:
            log.error(f"Failed to decrement training points: {e}")
            raise e
