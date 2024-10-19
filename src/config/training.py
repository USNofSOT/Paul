from datetime import datetime
from typing import Final

from src.config.main_server import NRC_RECORDS_CHANNEL
from src.config.netc_server import JLA_RECORDS_CHANNEL, SNLA_RECORDS_CHANNEL, OCS_RECORDS_CHANNEL, SOCS_RECORDS_CHANNEL

# FROM WHAT DATE THE TRAINING RECORDS SHOULD BE POPULATED (THIS IS THE DATE AFTER THE INITIAL TRAINING RECORDS ARE INSERTED)
TRAINING_POPULATE_FROM_DATE: Final[datetime] = datetime(2024, 10, 18)
# An aggregate of all training records channels
ALL_TRAINING_RECORDS_CHANNELS: Final[tuple[int, int, int, int, int]] = NRC_RECORDS_CHANNEL, JLA_RECORDS_CHANNEL, SNLA_RECORDS_CHANNEL, OCS_RECORDS_CHANNEL, SOCS_RECORDS_CHANNEL
