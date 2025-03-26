import os
from typing import Final

# TOKEN
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

# GUILD ID For Main Server
GUILD_ID: Final[int] = 933907909954371654
# NOTE: If changed also change in data/models/award_model.py

# GUILD OWNER ID
GUILD_OWNER_ID: Final[int] = 215990848465141760

# VOYAGE LOG CHANNEL
VOYAGE_LOGS: Final[int] = 935343526626078850

# NCO COMMS
NCO_COMMS: Final[int] = 935682287918546966

# NRC RECORDS CHANNEL
NRC_RECORDS_CHANNEL: Final[int] = 1023382640633581628

# BOAT COMMAND CHANNEL ID'S
BC_LUSTY: Final[int] = 995297017439977625
BC_VALHALLA: Final[int] = 1164680390204739674
BC_MAELSTROM: Final[int] = 1002304943291641896
BC_ADUN: Final[int] = 1240784666835943525
BC_ADRESTIA: Final[int] = 1084452484392697936
BC_HYPERION: Final[int] = 1157426343777157270
BC_PLATYPUS: Final[int] = 995299008987803719
BC_ARIZONA: Final[int] = 1058850504630866050
BC_PHANTOM: Final[int] = 1274254041823580225
BC_SILVERCLAW: Final[int] = 995299843448770690
BC_VENOM: Final[int] = 1237840915914297414
BC_TITAN: Final[int] = 1247403752210694197

# BOA is a side channel so that bot does not need to be in main boa channel
BC_BOA: Final[int] = 1101193993909456956

# Bot Status Channel
BOT_STATUS: Final[int] = 1296034003480215552
