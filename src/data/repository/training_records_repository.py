import logging
from datetime import datetime
from typing import Type

from sqlalchemy.orm import sessionmaker

from src.config import NETC_RECORDS_CHANNELS, SNLA_RECORDS_CHANNEL, JLA_RECORDS_CHANNEL, \
    SOCS_RECORDS_CHANNEL, OCS_RECORDS_CHANNEL, NRC_RECORDS_CHANNEL, SNLA_GRADUATE_ROLE, JLA_GRADUATE_ROLE, \
    OCS_GRADUATE_ROLE, SOCS_GRADUATE_ROLE
from src.data import engine, TrainingRecord, Sailor, Training, TraingType, TrainingCategory

log = logging.getLogger(__name__)
Session = sessionmaker(bind=engine)

class TrainingRecordsRepository:
    def __init__(self):
        self.session = Session()

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def set_graduation(self, target_id: int, role_id: int) -> TrainingRecord:
        timestamp = datetime.now()
        try:
            training_record: TrainingRecord = self.get_or_create_training_record(target_id)
            if role_id == SNLA_GRADUATE_ROLE:
                training_record.snla_graduation_date = timestamp
            elif role_id == JLA_GRADUATE_ROLE:
                training_record.jla_graduation_date = timestamp
            elif role_id == OCS_GRADUATE_ROLE:
                training_record.ocs_graduation_date = timestamp
            elif role_id == SOCS_GRADUATE_ROLE:
                training_record.socs_graduation_date = timestamp
            self.session.commit()
            return training_record
        except Exception as e:
            log.error(f"Failed to set graduation: {e}")
            raise e

    def remove_graduation(self, target_id: int, role_id: int):
        try:
            training_record: TrainingRecord = self.get_or_create_training_record(target_id)
            if role_id == SNLA_GRADUATE_ROLE:
                training_record.snla_graduation_date = None
            elif role_id == JLA_GRADUATE_ROLE:
                training_record.jla_graduation_date = None
            elif role_id == OCS_GRADUATE_ROLE:
                training_record.ocs_graduation_date = None
            elif role_id == SOCS_GRADUATE_ROLE:
                training_record.socs_graduation_date = None
            self.session.commit()
            return training_record
        except Exception as e:
            log.error(f"Failed to remove graduation: {e}")
            raise e

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
            training_record = self.get_or_create_training_record(target_id)

            # 1. Check if the training already exists
            training = self.session.query(Training).filter(Training.log_id == log_id).first()
            if training:
                raise ValueError("Training record already exists")

            # 2. Create a new training record
            training_category = TrainingCategory.NETC if log_channel_id in NETC_RECORDS_CHANNELS else TrainingCategory.NRC
            training_type_map = {
                JLA_RECORDS_CHANNEL: TraingType.JLA,
                SNLA_RECORDS_CHANNEL: TraingType.SNLA,
                OCS_RECORDS_CHANNEL: TraingType.OCS,
                SOCS_RECORDS_CHANNEL: TraingType.SOCS,
                NRC_RECORDS_CHANNEL: TraingType.NRC,
            }
            training_type = training_type_map.get(log_channel_id, TraingType.NRC)
            training = Training(log_id=log_id, target_id=target_id, log_channel_id=log_channel_id, log_time=log_time, training_type=training_type, training_category=training_category)
            self.session.add(training)
            self.session.commit()

            # 3. Check which NETC/NRC channel the training was logged in
            if log_channel_id in NETC_RECORDS_CHANNELS:
                self._increment_netc_training_points(target_id, 1)
            elif log_channel_id == NRC_RECORDS_CHANNEL:
                self._increment_nrc_training_points(target_id, 1)

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

            # 3. Check which NETC/NRC channel the training was logged in
            if log_channel_id in NETC_RECORDS_CHANNELS:
                self._decrement_netc_training_points(target_id, 1)
            elif log_channel_id == NRC_RECORDS_CHANNEL:
                self._decrement_nrc_training_points(target_id, 1)

            # 4. Return the training record
            return training
        except Exception as e:
            self.session.rollback()
            log.error(f"Failed to delete training: {e}")
            raise e

    def _increment_nrc_training_points(self, target_id: int, amount: int):
        try:
            training_record = self.get_or_create_training_record(target_id)
            # Make sure the points are not negative
            training_record.nrc_training_points = max(0, training_record.nrc_training_points + amount)
            self.session.commit()
        except Exception as e:
            log.error(f"Failed to increment NRC training points: {e}")
            raise e

    def _decrement_nrc_training_points(self, target_id: int, amount: int):
        try:
            training_record = self.get_or_create_training_record(target_id)
            # Make sure the value is decremented but doesn't go below 0
            training_record.nrc_training_points = max(0, training_record.nrc_training_points - amount)
            self.session.commit()
        except Exception as e:
            log.error(f"Failed to decrement NRC training points: {e}")
            raise e

    def _increment_netc_training_points(self, target_id: int, amount: int):
        try:
            training_record = self.get_or_create_training_record(target_id)
            # Make sure the points are not negative
            training_record.netc_training_points = max(0, training_record.netc_training_points + amount)
            self.session.commit()
        except Exception as e:
            log.error(f"Failed to increment NETC training points: {e}")
            raise

    def _decrement_netc_training_points(self, target_id: int, amount: int):
        try:
            training_record = self.get_or_create_training_record(target_id)
            # Make sure the value is decremented but doesn't go below 0
            training_record.netc_training_points = max(0, training_record.netc_training_points - amount)
            self.session.commit()
        except Exception as e:
            log.error(f"Failed to decrement NETC training points: {e}")
            raise e