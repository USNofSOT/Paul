from src.config.main_server import (BC_ADRESTIA, BC_ORIGIN, BC_MAELSTROM, BC_LUSTY, BC_VENOM, BC_AUDACIOUS, BC_ADUN,
                                    BC_HYPERION, BC_PLATYPUS, BC_ARIZONA, BC_PHANTOM, BC_COLLINS)
from src.data.structs import Ship

ROLE_ID_LUSTY = 933919139700019222
ROLE_ID_AUDACIOUS = 1164671319338664007
ROLE_ID_MAELSTROM = 1002303636522680391
ROLE_ID_ADUN = 1242143582463332402
ROLE_ID_ADRESTIA = 1084451910578339880
ROLE_ID_HYPERION = 1157426517912076318
ROLE_ID_PLATYPUS = 967531117882261536
ROLE_ID_ARIZONA = 1058840733248933908
ROLE_ID_PHANTOM = 1274251672876617792
ROLE_ID_ORIGIN = 977935623774162954
ROLE_ID_VENOM = 1237838106711822457
ROLE_ID_COLLINS = 1247405133130764329

###############################################################################
# Ships - Ship objects
###############################################################################
SHIPS = [
    Ship(
        name="USS Illustrious",
        boat_command_channel_id=BC_LUSTY,
        role_id=ROLE_ID_LUSTY
    ),
    Ship(
        name="USS Audacious",
        boat_command_channel_id=BC_AUDACIOUS,
        role_id=ROLE_ID_AUDACIOUS,
    ),
    Ship(
        name="USS Maelstrom",
        boat_command_channel_id=BC_MAELSTROM,
        role_id=ROLE_ID_MAELSTROM,
    ),
    Ship(
        name="USS Adun",
        boat_command_channel_id=BC_ADUN,
        role_id=ROLE_ID_ADUN,
    ),
    Ship(
        name="USS Adrestia",
        boat_command_channel_id=BC_ADRESTIA,
        role_id=ROLE_ID_ADRESTIA,
    ),
    Ship(
        name="USS Hyperion",
        boat_command_channel_id=BC_HYPERION,
        role_id=ROLE_ID_HYPERION,
    ),
    Ship(
        name="USS Platypus",
        boat_command_channel_id=BC_PLATYPUS,
        role_id=ROLE_ID_PLATYPUS
    ),
    Ship(
        name="USS Arizona",
        boat_command_channel_id=BC_ARIZONA,
        role_id=ROLE_ID_ARIZONA,
    ),
    Ship(
        name="USS Phantom",
        boat_command_channel_id=BC_PHANTOM,
        role_id=ROLE_ID_PHANTOM,
    ),
    Ship(
        name="USS Origin",
        boat_command_channel_id=BC_ORIGIN,
        role_id=ROLE_ID_ORIGIN,
    ),
    Ship(
        name="USS Venom",
        boat_command_channel_id=BC_VENOM,
        role_id=ROLE_ID_VENOM,
    ),
    Ship(
        name="USS Collins",
        boat_command_channel_id=BC_COLLINS,
        role_id=ROLE_ID_COLLINS,
    ),
]