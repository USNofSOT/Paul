from datetime import datetime
from typing import Final

from src.config.main_server import NRC_RECORDS_CHANNEL
from src.config.netc_server import ALL_NETC_RECORDS_CHANNELS
from src.config.spd_servers import ST_RECORDS_CHANNEL

# FROM WHAT DATE THE TRAINING RECORDS SHOULD BE POPULATED (THIS IS THE DATE AFTER THE INITIAL TRAINING RECORDS ARE INSERTED)
TRAINING_POPULATE_FROM_DATE: Final[datetime] = datetime(2024, 10, 19, 15, 0, 0)
# Keep legacy NETC channels in the aggregate so historical records remain
# visible to ingest/deletion flows even after they leave the active curriculum list.
ALL_TRAINING_RECORDS_CHANNELS: Final[tuple[int, ...]] = (
    NRC_RECORDS_CHANNEL,
    *ALL_NETC_RECORDS_CHANNELS,
    ST_RECORDS_CHANNEL,
)
